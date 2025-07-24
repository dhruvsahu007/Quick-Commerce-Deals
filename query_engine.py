import sqlite3
import pandas as pd
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# LangChain imports
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()

class QueryEngine:
    def __init__(self):
        """Initialize the query engine with LangChain SQL agents and RAG."""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        
        # Set environment variable for LangChain
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        
        # Database paths
        self.databases = {
            'zepto': os.path.join('databases', 'zepto.db'),
            'blinkit': os.path.join('databases', 'blinkit.db'),
            'swiggy': os.path.join('databases', 'swiggy.db')
        }
        
        # Initialize LangChain components
        self._initialize_langchain_components()
    
    def _initialize_langchain_components(self):
        """Initialize LangChain SQL databases, agents, and RAG components."""
        try:
            # Load SQLite databases
            self.zepto_db = SQLDatabase.from_uri(f"sqlite:///{self.databases['zepto']}")
            self.blinkit_db = SQLDatabase.from_uri(f"sqlite:///{self.databases['blinkit']}")
            self.swiggy_db = SQLDatabase.from_uri(f"sqlite:///{self.databases['swiggy']}")
            
            # Prepare LLM
            self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
            
            # Create toolkits for each database
            self.zepto_toolkit = SQLDatabaseToolkit(db=self.zepto_db, llm=self.llm)
            self.blinkit_toolkit = SQLDatabaseToolkit(db=self.blinkit_db, llm=self.llm)
            self.swiggy_toolkit = SQLDatabaseToolkit(db=self.swiggy_db, llm=self.llm)
            
            # Build schema descriptions for RAG
            self._setup_rag_system()
            
            # Create SQL agents for each database
            self.zepto_agent = create_sql_agent(
                llm=self.llm,
                toolkit=self.zepto_toolkit,
                verbose=False,
                handle_parsing_errors=True
            )
            
            self.blinkit_agent = create_sql_agent(
                llm=self.llm,
                toolkit=self.blinkit_toolkit,
                verbose=False,
                handle_parsing_errors=True
            )
            
            self.swiggy_agent = create_sql_agent(
                llm=self.llm,
                toolkit=self.swiggy_toolkit,
                verbose=False,
                handle_parsing_errors=True
            )
            
        except Exception as e:
            raise Exception(f"Failed to initialize LangChain components: {str(e)}")
    
    def _extract_schema_docs(self, db: SQLDatabase, db_name: str) -> str:
        """Extract schema information from a database."""
        schema_info = ""
        table_names = db.get_usable_table_names()
        
        for table in table_names:
            schema_info += f"\n\n[{db_name}] Table: {table}\n"
            schema_info += db.get_table_info([table])
        
        return schema_info
    
    def _setup_rag_system(self):
        """Set up RAG system for schema information."""
        try:
            # Extract schema information from all databases
            zepto_schema = self._extract_schema_docs(self.zepto_db, "Zepto")
            blinkit_schema = self._extract_schema_docs(self.blinkit_db, "Blinkit")
            swiggy_schema = self._extract_schema_docs(self.swiggy_db, "Swiggy")
            
            # Combine all schema information
            combined_schema = zepto_schema + "\n\n" + blinkit_schema + "\n\n" + swiggy_schema
            
            # Create documents and embeddings
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=50)
            docs = text_splitter.create_documents([combined_schema])
            
            # Create FAISS vectorstore
            self.vectorstore = FAISS.from_documents(docs, OpenAIEmbeddings())
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            
        except Exception as e:
            print(f"Warning: Failed to setup RAG system: {str(e)}")
            self.retriever = None
    
    def _add_context_to_query(self, query: str) -> str:
        """Add RAG context to the user query."""
        if self.retriever is None:
            return query
        
        try:
            related_docs = self.retriever.get_relevant_documents(query)
            context = "\n\n".join([doc.page_content for doc in related_docs])
            return f"Use the following context to answer:\n{context}\n\nQuestion: {query}"
        except:
            return query
    
    def _determine_databases_needed(self, question: str) -> List[str]:
        """Determine which databases need to be queried based on the question."""
        question_lower = question.lower()
        
        # Check for specific platform mentions
        platforms = []
        if 'zepto' in question_lower:
            platforms.append('zepto')
        if 'blinkit' in question_lower:
            platforms.append('blinkit')
        if 'swiggy' in question_lower or 'instamart' in question_lower:
            platforms.append('swiggy')
        
        # If no specific platform mentioned, use all for comparison queries
        if not platforms:
            comparison_keywords = ['compare', 'cheapest', 'most expensive', 'best price', 'across', 'between']
            if any(keyword in question_lower for keyword in comparison_keywords):
                platforms = ['zepto', 'blinkit', 'swiggy']
            else:
                platforms = ['zepto', 'blinkit', 'swiggy']  # Default to all
        
        return platforms
    
    def _query_database(self, agent, db_name: str, question: str) -> Dict[str, Any]:
        """Query a specific database using its agent."""
        try:
            enriched_query = self._add_context_to_query(question)
            response = agent.invoke({"input": enriched_query})
            
            return {
                'success': True,
                'result': response.get('output', ''),
                'platform': db_name.capitalize(),
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'result': '',
                'platform': db_name.capitalize(),
                'error': str(e)
            }
    
    def process_user_question(self, user_question: str) -> Dict[str, Any]:
        """Process user question using LangChain SQL agents."""
        try:
            # Determine which databases to query
            databases_needed = self._determine_databases_needed(user_question)
            
            # Query results from different databases
            individual_results = {}
            all_responses = []
            
            for db_name in databases_needed:
                if db_name == 'zepto':
                    result = self._query_database(self.zepto_agent, db_name, user_question)
                elif db_name == 'blinkit':
                    result = self._query_database(self.blinkit_agent, db_name, user_question)
                elif db_name == 'swiggy':
                    result = self._query_database(self.swiggy_agent, db_name, user_question)
                
                individual_results[db_name] = result
                if result['success']:
                    all_responses.append(f"[{result['platform']}]: {result['result']}")
            
            # Generate combined answer summary
            answer_summary = self._generate_answer_summary(user_question, individual_results, all_responses)
            
            # Create explanation
            successful_queries = [db for db, result in individual_results.items() if result['success']]
            explanation = f"Successfully queried {len(successful_queries)} database(s): {', '.join(db.capitalize() for db in successful_queries)}"
            
            return {
                'individual_results': individual_results,
                'combined_results': None,  # We'll use individual_results for display
                'answer_summary': answer_summary,
                'explanation': explanation,
                'databases_queried': databases_needed,
                'success': len(successful_queries) > 0
            }
            
        except Exception as e:
            return {
                'individual_results': {},
                'combined_results': None,
                'answer_summary': f'Sorry, I encountered an error while processing your question: {str(e)}',
                'explanation': f'Error processing question: {str(e)}',
                'databases_queried': [],
                'success': False
            }
    
    def _generate_answer_summary(self, user_question: str, individual_results: Dict, all_responses: List[str]) -> str:
        """Generate a concise one-line answer based on the agent responses."""
        if not all_responses:
            return "No results found for your query."
        
        try:
            # Combine all responses for analysis
            combined_response = "\n\n".join(all_responses)
            
            prompt = f"""
            Based on the following database query results from different quick commerce platforms, provide a clear, concise one-line answer to the user's question.
            
            User Question: "{user_question}"
            
            Database Results:
            {combined_response}
            
            Instructions:
            - Give a direct, specific answer in one sentence
            - Include the platform name and specific details when relevant
            - For price comparisons, mention the cheapest/most expensive with actual prices
            - For availability questions, mention which platforms have the items
            - Be conversational and helpful
            - If multiple platforms have similar results, summarize appropriately
            
            Examples:
            - "Zepto has the cheapest onions at ₹28.50"
            - "Blinkit offers the most expensive apples at ₹135.00, while Swiggy has the cheapest at ₹145.00"
            - "All three platforms have fruits available with competitive pricing"
            
            Answer:"""
            
            response = self.llm.invoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            return f"I found some results for you, but couldn't generate a summary. Please check the detailed results below."
    
    def get_sample_questions(self) -> List[str]:
        """Return sample questions users can ask."""
        return [
            "Which app has the cheapest onions?",
            "Compare apple prices between all platforms",
            "Show me all fruits available on Zepto",
            "What are the most expensive items on Blinkit?",
            "Find products with more than 20% discount",
            "Compare milk prices across all apps",
            "Show me all snacks under 30 rupees",
            "Which platform has the best vegetable prices?",
            "Find organic products available",
            "Show products not available on any platform"
        ]
