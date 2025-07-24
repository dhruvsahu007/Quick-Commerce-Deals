import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from query_engine import QueryEngine
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Quick Commerce Price Comparison",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .platform-metric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .sample-question {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.25rem 0;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_query_engine():
    """Initialize and cache the query engine."""
    try:
        return QueryEngine()
    except Exception as e:
        st.error(f"Failed to initialize query engine: {str(e)}")
        return None

def display_database_status():
    """Display the status of database files."""
    st.sidebar.markdown("### 📊 Database Status")
    
    databases = ['zepto.db', 'blinkit.db', 'swiggy.db']
    for db in databases:
        db_path = os.path.join('databases', db)
        if os.path.exists(db_path):
            st.sidebar.success(f"✅ {db}")
        else:
            st.sidebar.error(f"❌ {db}")

def display_sample_questions(query_engine):
    """Display sample questions in the sidebar."""
    st.sidebar.markdown("### 💡 Sample Questions")
    st.sidebar.markdown("Click on any question below to try it:")
    
    sample_questions = query_engine.get_sample_questions()
    
    for i, question in enumerate(sample_questions):
        if st.sidebar.button(f"🔍 {question}", key=f"sample_{i}"):
            st.session_state.user_question = question
            st.rerun()

def create_price_comparison_chart(df):
    """Create a price comparison chart."""
    if df is None or df.empty:
        return None
    
    if 'price' in df.columns and 'platform' in df.columns:
        fig = px.bar(
            df, 
            x='name', 
            y='price', 
            color='platform',
            title="Price Comparison Across Platforms",
            labels={'price': 'Price (₹)', 'name': 'Product Name'},
            height=400
        )
        fig.update_layout(xaxis_tickangle=-45)
        return fig
    return None

def create_discount_chart(df):
    """Create a discount percentage chart."""
    if df is None or df.empty or 'discount_percentage' not in df.columns:
        return None
    
    fig = px.scatter(
        df,
        x='price',
        y='discount_percentage',
        color='platform',
        size='discount_percentage',
        hover_data=['name', 'category'],
        title="Discount vs Price Analysis",
        labels={'price': 'Price (₹)', 'discount_percentage': 'Discount (%)'},
        height=400
    )
    return fig

def display_results(results):
    """Display query results with visualizations."""
    if not results['success']:
        st.error(f"❌ {results['explanation']}")
        return
    
    st.success(f"✅ {results['explanation']}")
    
    # Display individual platform results from LangChain agents
    if results['individual_results']:
        st.markdown("### 🏪 Platform-wise Results")
        
        for platform, result_data in results['individual_results'].items():
            platform_name = platform.capitalize()
            
            if result_data['success']:
                with st.expander(f"📱 {platform_name} Results", expanded=True):
                    st.markdown("**Agent Response:**")
                    st.write(result_data['result'])
            else:
                with st.expander(f"❌ {platform_name} - Error"):
                    st.error(f"Error: {result_data['error']}")
    
    # Show databases queried
    if results.get('databases_queried'):
        st.markdown("### 🔍 Databases Queried")
        databases_info = ", ".join([db.capitalize() for db in results['databases_queried']])
        st.info(f"Queried databases: {databases_info}")
    
    # Note about the new approach
    st.markdown("### ℹ️ Query Method")
    st.info("🤖 Using LangChain SQL Agents with RAG-enhanced context and tool calling for intelligent database queries.")

def main():
    """Main Streamlit app function."""
    # Header
    st.markdown('<h1 class="main-header">🛒 Quick Commerce Price Comparison</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'user_question' not in st.session_state:
        st.session_state.user_question = ""
    
    # Initialize query engine
    query_engine = initialize_query_engine()
    
    if query_engine is None:
        st.error("❌ Failed to initialize the application. Please check your OpenAI API key in the .env file.")
        st.stop()
    
    # Sidebar
    display_database_status()
    display_sample_questions(query_engine)
    
    # Main content area
    st.markdown("### 🔍 Ask Your Question")
    st.markdown("Compare prices, find deals, and discover the best offers across Zepto, Blinkit, and Swiggy Instamart!")
    
    # Question input
    user_question = st.text_input(
        "Enter your question:",
        value=st.session_state.user_question,
        placeholder="e.g., Which app has the cheapest onions?",
        key="question_input"
    )
    
    # Search button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Process question
    if search_button and user_question.strip():
        with st.spinner("🤔 Analyzing your question and querying databases..."):
            results = query_engine.process_user_question(user_question.strip())
            
            # Display AI Answer Summary
            if results.get('answer_summary'):
                st.markdown("### 🤖 AI Answer")
                if results['success']:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 1.5rem;
                        border-radius: 10px;
                        margin: 1rem 0;
                        font-size: 1.2rem;
                        font-weight: 500;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    ">
                        💡 {results['answer_summary']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ {results['answer_summary']}")
            
            # Display detailed results
            display_results(results)
    
    elif search_button and not user_question.strip():
        st.warning("⚠️ Please enter a question to search.")
    
    # Information section
    st.markdown("---")
    st.markdown("### ℹ️ About This App")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Features:**
        - 🔍 Natural language queries
        - 📊 Price comparisons across platforms
        - 💰 Discount analysis
        - 📈 Interactive visualizations
        - 🏪 Platform-wise breakdowns
        """)
    
    with col2:
        st.markdown("""
        **Platforms:**
        - 🟢 **Zepto** - Quick 10-minute delivery
        - 🔵 **Blinkit** - Instant grocery delivery  
        - 🟠 **Swiggy Instamart** - Food & grocery delivery
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #666;">Built with ❤️ using Streamlit, OpenAI, and SQLite</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
