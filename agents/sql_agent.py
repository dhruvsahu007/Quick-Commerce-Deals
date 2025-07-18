from typing import Dict, List, Any, Optional
import json
import time
from datetime import datetime, timedelta
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms.openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from agents.schema_analyzer import SchemaAnalyzer, QueryPlanner
from cache.query_cache import QueryCache
from monitoring.performance import QueryMonitor
from database.connection import get_db_session
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class AdvancedSQLAgent:
    """Advanced SQL agent with intelligent query generation and optimization"""
    
    def __init__(self):
        self.db_session = get_db_session()
        self.schema_analyzer = SchemaAnalyzer()
        self.query_planner = QueryPlanner()
        self.cache = QueryCache()
        self.monitor = QueryMonitor()
        self.llm = self._initialize_llm()
        self.sql_database = self._initialize_sql_database()
        self.agent = self._create_agent()
        
    def _initialize_llm(self):
        """Initialize Language Model"""
        try:
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                openai_api_key=Config.OPENAI_API_KEY,
                max_tokens=2000
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {e}")
            # Fallback to a mock LLM for demo purposes
            return MockLLM()
    
    def _initialize_sql_database(self):
        """Initialize SQL Database connection for LangChain"""
        return SQLDatabase.from_uri(Config.DATABASE_URL)
    
    def _create_agent(self):
        """Create SQL agent with custom toolkit"""
        try:
            toolkit = SQLDatabaseToolkit(
                db=self.sql_database,
                llm=self.llm
            )
            
            return create_sql_agent(
                llm=self.llm,
                toolkit=toolkit,
                verbose=True,
                max_iterations=5,
                max_execution_time=Config.QUERY_TIMEOUT,
                return_intermediate_steps=True
            )
        except Exception as e:
            logger.error(f"Failed to create SQL agent: {e}")
            return None
    
    def process_natural_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process natural language query and return results"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self.cache.generate_cache_key(query, context)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached result")
                return cached_result
            
            # Analyze query and create plan
            query_plan = self.query_planner.create_query_plan(query)
            
            # Validate query plan
            is_valid, issues = self.query_planner.validate_query_plan(query_plan)
            if not is_valid:
                return {
                    'success': False,
                    'error': f"Query validation failed: {'; '.join(issues)}",
                    'suggestions': self._generate_suggestions(query, issues)
                }
            
            # Generate SQL query
            sql_query = self._generate_sql_query(query, query_plan)
            
            if not sql_query:
                return {
                    'success': False,
                    'error': "Failed to generate SQL query",
                    'original_query': query
                }
            
            # Execute query with monitoring
            execution_result = self._execute_monitored_query(sql_query, query_plan)
            
            # Process and format results
            formatted_results = self._format_results(execution_result, query)
            
            # Prepare response
            response = {
                'success': True,
                'query': query,
                'sql_query': sql_query,
                'results': formatted_results,
                'execution_time': time.time() - start_time,
                'plan': {
                    'tables_used': query_plan.tables,
                    'complexity_score': query_plan.complexity_score,
                    'estimated_cost': query_plan.estimated_cost
                },
                'metadata': {
                    'total_rows': len(formatted_results) if formatted_results else 0,
                    'cached': False
                }
            }
            
            # Cache successful results
            if response['success']:
                self.cache.set(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            return {
                'success': False,
                'error': str(e),
                'original_query': query,
                'execution_time': time.time() - start_time
            }
    
    def _generate_sql_query(self, natural_query: str, query_plan) -> Optional[str]:
        """Generate SQL query using LLM with query plan guidance"""
        
        # Create enhanced prompt with schema information
        prompt_template = """
        You are an expert SQL query generator for a quick commerce price comparison platform.
        
        Database Schema Information:
        {schema_info}
        
        Query Plan:
        - Tables to use: {tables}
        - Suggested joins: {joins}
        - Conditions to consider: {conditions}
        
        Natural Language Query: "{natural_query}"
        
        Generate a SQL query that:
        1. Uses the suggested tables and joins
        2. Applies relevant filters and conditions
        3. Returns meaningful results for price comparison
        4. Limits results to {max_results} rows for performance
        5. Includes relevant columns like product name, platform name, price, discounts
        
        SQL Query:
        """
        
        schema_info = self._build_schema_context(query_plan.tables)
        
        prompt = prompt_template.format(
            schema_info=schema_info,
            tables=", ".join(query_plan.tables),
            joins="; ".join(query_plan.joins),
            conditions="; ".join(query_plan.conditions),
            natural_query=natural_query,
            max_results=Config.MAX_RESULT_SIZE
        )
        
        try:
            if self.agent:
                # Use LangChain agent
                result = self.agent.run(natural_query)
                return self._extract_sql_from_agent_result(result)
            else:
                # Fallback to template-based generation
                return self._generate_template_sql(natural_query, query_plan)
                
        except Exception as e:
            logger.error(f"LLM query generation failed: {e}")
            return self._generate_template_sql(natural_query, query_plan)
    
    def _build_schema_context(self, tables: List[str]) -> str:
        """Build schema context for LLM prompt"""
        schema_parts = []
        
        for table in tables:
            table_info = self.schema_analyzer.tables_info.get(table)
            if table_info:
                columns = ", ".join(table_info.columns[:10])  # Limit columns for prompt
                schema_parts.append(f"{table}: {table_info.description}\n  Columns: {columns}")
        
        return "\n".join(schema_parts)
    
    def _extract_sql_from_agent_result(self, result: str) -> Optional[str]:
        """Extract SQL query from agent result"""
        # Look for SQL pattern in result
        import re
        sql_patterns = [
            r'```sql\n(.*?)\n```',
            r'```\n(SELECT.*?);?\n```',
            r'(SELECT.*?);?$'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, result, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, assume the whole result is SQL
        if 'SELECT' in result.upper():
            return result.strip()
        
        return None
    
    def _generate_template_sql(self, natural_query: str, query_plan) -> str:
        """Generate SQL using template-based approach as fallback"""
        query_lower = natural_query.lower()
        
        # Basic SELECT clause
        select_cols = [
            "products.name as product_name",
            "platforms.display_name as platform",
            "product_prices.current_price as price",
            "product_prices.original_price",
            "product_prices.discount_percentage",
            "product_prices.is_available"
        ]
        
        # Basic FROM clause
        main_table = "products"
        joins = [
            "JOIN product_prices ON products.id = product_prices.product_id",
            "JOIN platforms ON product_prices.platform_id = platforms.id"
        ]
        
        # Add category join if needed
        if 'categories' in query_plan.tables:
            joins.append("JOIN categories ON products.category_id = categories.id")
            select_cols.append("categories.display_name as category")
        
        # Add brand join if needed
        if 'brands' in query_plan.tables:
            joins.append("JOIN brands ON products.brand_id = brands.id")
            select_cols.append("brands.display_name as brand")
        
        # WHERE conditions
        where_conditions = ["product_prices.is_available = 1"]
        where_conditions.extend(query_plan.conditions)
        
        # ORDER BY
        order_by = "product_prices.current_price ASC"
        if 'expensive' in query_lower:
            order_by = "product_prices.current_price DESC"
        elif 'popular' in query_lower:
            order_by = "products.name ASC"
        
        # Construct query
        sql_query = f"""
        SELECT {', '.join(select_cols)}
        FROM {main_table}
        {' '.join(joins)}
        WHERE {' AND '.join(where_conditions)}
        ORDER BY {order_by}
        LIMIT {Config.MAX_RESULT_SIZE}
        """
        
        return sql_query.strip()
    
    def _execute_monitored_query(self, sql_query: str, query_plan) -> List[Dict[str, Any]]:
        """Execute query with performance monitoring"""
        monitor_id = self.monitor.start_query_monitoring(sql_query, query_plan)
        
        try:
            from sqlalchemy import text
            result = self.db_session.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            self.monitor.end_query_monitoring(monitor_id, True, len(data))
            return data
            
        except Exception as e:
            self.monitor.end_query_monitoring(monitor_id, False, 0, str(e))
            raise
    
    def _format_results(self, results: List[Dict[str, Any]], original_query: str) -> List[Dict[str, Any]]:
        """Format and enhance query results"""
        if not results:
            return []
        
        formatted_results = []
        for row in results:
            formatted_row = {}
            
            # Format common fields
            for key, value in row.items():
                if 'price' in key.lower() and isinstance(value, (int, float)):
                    formatted_row[key] = f"₹{value:.2f}"
                elif 'percentage' in key.lower() and isinstance(value, (int, float)):
                    formatted_row[key] = f"{value:.1f}%"
                elif key.lower() == 'is_available':
                    formatted_row[key] = "Available" if value else "Out of Stock"
                else:
                    formatted_row[key] = value
            
            # Add calculated fields
            if 'discount_percentage' in row and isinstance(row['discount_percentage'], (int, float)):
                if row['discount_percentage'] > 0:
                    formatted_row['deal_quality'] = self._assess_deal_quality(row['discount_percentage'])
            
            formatted_results.append(formatted_row)
        
        return formatted_results
    
    def _assess_deal_quality(self, discount_percentage: float) -> str:
        """Assess quality of deal based on discount percentage"""
        if discount_percentage >= 30:
            return "Excellent Deal"
        elif discount_percentage >= 20:
            return "Good Deal"
        elif discount_percentage >= 10:
            return "Fair Deal"
        else:
            return "Regular Price"
    
    def _generate_suggestions(self, query: str, issues: List[str]) -> List[str]:
        """Generate suggestions for improving the query"""
        suggestions = []
        
        if "complexity too high" in " ".join(issues).lower():
            suggestions.append("Try breaking down your query into smaller, more specific questions")
            suggestions.append("Focus on a specific product or category")
        
        if "too many tables" in " ".join(issues).lower():
            suggestions.append("Be more specific about what you're looking for")
            suggestions.append("Try searching for products in a specific category")
        
        if "high estimated cost" in " ".join(issues).lower():
            suggestions.append("Add filters like price range or specific platform")
            suggestions.append("Search for a specific product instead of browsing all products")
        
        # Generic suggestions
        suggestions.extend([
            "Try: 'Which app has cheapest onions right now?'",
            "Try: 'Show products with 30% discount on Blinkit'",
            "Try: 'Compare apple prices between Zepto and Instamart'"
        ])
        
        return suggestions
    
    def get_popular_queries(self) -> List[str]:
        """Get list of popular/sample queries"""
        return [
            "Which app has cheapest onions right now?",
            "Show products with 30% discount on Blinkit",
            "Compare fruit prices between Zepto and Instamart", 
            "Find best deals for ₹1000 grocery list",
            "Show me all milk prices across platforms",
            "Which platform has the best discounts today?",
            "Find organic products under ₹200",
            "Compare delivery charges across platforms",
            "Show trending products this week",
            "Find products with highest discount percentage"
        ]

class MockLLM:
    """Mock LLM for when OpenAI is not available"""
    
    def invoke(self, prompt: str) -> str:
        return self._generate_mock_response(prompt)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate a mock SQL response based on prompt analysis"""
        prompt_lower = prompt.lower()
        
        if 'cheapest' in prompt_lower or 'lowest price' in prompt_lower:
            return """
            SELECT products.name as product_name, platforms.display_name as platform, 
                   product_prices.current_price as price
            FROM products 
            JOIN product_prices ON products.id = product_prices.product_id
            JOIN platforms ON product_prices.platform_id = platforms.id
            WHERE product_prices.is_available = 1
            ORDER BY product_prices.current_price ASC
            LIMIT 10
            """
        elif 'discount' in prompt_lower:
            return """
            SELECT products.name as product_name, platforms.display_name as platform,
                   product_prices.current_price as price, product_prices.discount_percentage
            FROM products 
            JOIN product_prices ON products.id = product_prices.product_id
            JOIN platforms ON product_prices.platform_id = platforms.id
            WHERE product_prices.discount_percentage > 0
            ORDER BY product_prices.discount_percentage DESC
            LIMIT 10
            """
        else:
            return """
            SELECT products.name as product_name, platforms.display_name as platform,
                   product_prices.current_price as price
            FROM products 
            JOIN product_prices ON products.id = product_prices.product_id
            JOIN platforms ON product_prices.platform_id = platforms.id
            WHERE product_prices.is_available = 1
            LIMIT 10
            """
