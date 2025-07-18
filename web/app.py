import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import time
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Quick Commerce Deals",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class QuickCommerceApp:
    def __init__(self):
        self.api_base_url = API_BASE_URL
        
    def make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make API request with error handling"""
        try:
            url = f"{self.api_base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the backend server is running.")
            return {"error": "Connection failed"}
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
            return {"error": "Timeout"}
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ API Error: {e}")
            return {"error": str(e)}
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            return {"error": str(e)}
    
    def render_header(self):
        """Render main header"""
        st.markdown('<div class="main-header">🛒 Quick Commerce Deals</div>', unsafe_allow_html=True)
        st.markdown("**Advanced price comparison platform for quick commerce apps**")
        st.markdown("---")
    
    def render_query_interface(self):
        """Render main query interface"""
        st.header("🔍 Natural Language Query")
        
        # Query input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "Ask anything about prices, deals, or products:",
                placeholder="e.g., Which app has cheapest onions right now?",
                help="Enter your question in natural language"
            )
        
        with col2:
            use_cache = st.checkbox("Use Cache", value=True, help="Use cached results for faster responses")
        
        # Popular queries
        st.subheader("💡 Popular Queries")
        popular_queries = self.get_popular_queries()
        
        if popular_queries and not popular_queries.get("error"):
            col1, col2, col3 = st.columns(3)
            cols = [col1, col2, col3]
            
            for i, sample_query in enumerate(popular_queries[:9]):
                with cols[i % 3]:
                    if st.button(sample_query, key=f"sample_{i}"):
                        query = sample_query
                        st.rerun()
        
        # Process query
        if query or st.button("🚀 Search", disabled=not query):
            if query:
                self.process_and_display_query(query, use_cache)
    
    def get_popular_queries(self) -> List[str]:
        """Get popular queries from API"""
        return self.make_api_request("/popular-queries")
    
    def process_and_display_query(self, query: str, use_cache: bool = True):
        """Process query and display results"""
        with st.spinner("🔄 Processing your query..."):
            # Make API request
            request_data = {
                "query": query,
                "use_cache": use_cache
            }
            
            result = self.make_api_request("/query", "POST", request_data)
            
            if result.get("error"):
                st.error(f"❌ Error: {result['error']}")
                return
            
            # Display results
            self.display_query_results(result)
    
    def display_query_results(self, result: Dict):
        """Display query results in an organized manner"""
        if not result.get("success"):
            st.error(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            
            # Show suggestions if available
            if result.get("suggestions"):
                st.subheader("💡 Suggestions")
                for suggestion in result["suggestions"]:
                    st.info(f"💡 {suggestion}")
            return
        
        # Success message
        st.success(f"✅ Query processed successfully in {result.get('execution_time', 0):.3f} seconds")
        
        # Display metadata
        metadata = result.get('metadata', {})
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Results Found", metadata.get('total_rows', 0))
        with col2:
            st.metric("Execution Time", f"{result.get('execution_time', 0):.3f}s")
        with col3:
            cached_status = "Yes" if metadata.get('cached') else "No"
            st.metric("From Cache", cached_status)
        with col4:
            plan = result.get('plan', {})
            st.metric("Complexity Score", plan.get('complexity_score', 0))
        
        # Display results table
        results_data = result.get('results', [])
        if results_data:
            st.subheader("📊 Results")
            
            # Convert to DataFrame
            df = pd.DataFrame(results_data)
            
            # Format the DataFrame for better display
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Create visualizations if applicable
            self.create_visualizations(df, result.get('query', ''))
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"quick_commerce_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Show SQL query in expander
        if result.get('sql_query'):
            with st.expander("🔍 View Generated SQL Query"):
                st.code(result['sql_query'], language='sql')
        
        # Show execution plan
        plan = result.get('plan', {})
        if plan:
            with st.expander("📋 Query Execution Plan"):
                col1, col2 = st.columns(2)
                with col1:
                    st.json({
                        "Tables Used": plan.get('tables_used', []),
                        "Complexity Score": plan.get('complexity_score', 0)
                    })
                with col2:
                    st.json({
                        "Estimated Cost": plan.get('estimated_cost', 0),
                        "Optimization": "Applied" if plan.get('complexity_score', 0) < 10 else "Needs Review"
                    })
    
    def create_visualizations(self, df: pd.DataFrame, query: str):
        """Create relevant visualizations based on data"""
        if df.empty:
            return
        
        query_lower = query.lower()
        
        # Price comparison chart
        if 'price' in df.columns or any('price' in col.lower() for col in df.columns):
            price_cols = [col for col in df.columns if 'price' in col.lower() and col != 'original_price']
            platform_col = next((col for col in df.columns if 'platform' in col.lower()), None)
            product_col = next((col for col in df.columns if 'product' in col.lower()), None)
            
            if price_cols and platform_col and len(df) > 1:
                st.subheader("📈 Price Comparison")
                
                # Clean price data (remove ₹ symbol and convert to float)
                df_viz = df.copy()
                for col in price_cols:
                    if df_viz[col].dtype == 'object':
                        df_viz[col] = df_viz[col].str.replace('₹', '').str.replace(',', '').astype(float)
                
                # Create bar chart
                fig = px.bar(
                    df_viz.head(10),  # Limit to top 10 for readability
                    x=product_col if product_col else platform_col,
                    y=price_cols[0],
                    color=platform_col if platform_col else None,
                    title="Price Comparison Across Platforms",
                    labels={price_cols[0]: "Price (₹)"}
                )
                
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Discount analysis
        if 'discount_percentage' in df.columns:
            st.subheader("💰 Discount Analysis")
            
            # Clean discount data
            df_viz = df.copy()
            if df_viz['discount_percentage'].dtype == 'object':
                df_viz['discount_percentage'] = df_viz['discount_percentage'].str.replace('%', '').astype(float)
            
            # Create histogram
            fig = px.histogram(
                df_viz,
                x='discount_percentage',
                nbins=20,
                title="Distribution of Discounts",
                labels={'discount_percentage': 'Discount %', 'count': 'Number of Products'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Platform distribution
        platform_col = next((col for col in df.columns if 'platform' in col.lower()), None)
        if platform_col and len(df) > 1:
            st.subheader("🏪 Platform Distribution")
            
            platform_counts = df[platform_col].value_counts()
            
            fig = px.pie(
                values=platform_counts.values,
                names=platform_counts.index,
                title="Results by Platform"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_advanced_search(self):
        """Render advanced search interface"""
        st.header("🔧 Advanced Search")
        
        # Get platforms and categories
        platforms = self.make_api_request("/platforms")
        categories = self.make_api_request("/categories")
        
        # Search form
        with st.form("advanced_search"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_query = st.text_input("Product Name", placeholder="e.g., onion, milk, apple")
                
                if categories and not categories.get("error"):
                    category_options = ["All Categories"] + [cat["display_name"] for cat in categories]
                    selected_category = st.selectbox("Category", category_options)
                else:
                    selected_category = "All Categories"
                
                min_price = st.number_input("Minimum Price (₹)", min_value=0.0, value=0.0, step=1.0)
            
            with col2:
                if platforms and not platforms.get("error"):
                    platform_options = ["All Platforms"] + [plat["display_name"] for plat in platforms]
                    selected_platform = st.selectbox("Platform", platform_options)
                else:
                    selected_platform = "All Platforms"
                
                max_price = st.number_input("Maximum Price (₹)", min_value=0.0, value=1000.0, step=1.0)
                limit = st.number_input("Max Results", min_value=1, max_value=100, value=20, step=1)
            
            search_submitted = st.form_submit_button("🔍 Search Products")
        
        if search_submitted:
            # Build search parameters
            params = {"limit": limit}
            
            if search_query:
                params["q"] = search_query
            
            if selected_category != "All Categories" and categories:
                category_id = next((cat["id"] for cat in categories if cat["display_name"] == selected_category), None)
                if category_id:
                    params["category_id"] = category_id
            
            if selected_platform != "All Platforms" and platforms:
                platform_id = next((plat["id"] for plat in platforms if plat["display_name"] == selected_platform), None)
                if platform_id:
                    params["platform_id"] = platform_id
            
            if min_price > 0:
                params["min_price"] = min_price
            
            if max_price > 0:
                params["max_price"] = max_price
            
            # Make search request
            with st.spinner("🔄 Searching..."):
                # Convert params to query string
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                results = self.make_api_request(f"/products/search?{query_string}")
                
                if results and not results.get("error"):
                    st.success(f"✅ Found {len(results)} products")
                    
                    if results:
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Create visualization
                        self.create_visualizations(df, f"Search: {search_query}")
                else:
                    st.warning("No products found matching your criteria")
    
    def render_monitoring_dashboard(self):
        """Render monitoring and analytics dashboard"""
        st.header("📊 Monitoring Dashboard")
        
        # Get monitoring data
        dashboard_data = self.make_api_request("/monitoring/dashboard")
        
        if dashboard_data.get("error"):
            st.error("❌ Failed to load monitoring data")
            return
        
        # Performance metrics
        st.subheader("⚡ Performance Metrics")
        perf_stats = dashboard_data.get("performance_stats", {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Queries", perf_stats.get("total_queries", 0))
        with col2:
            st.metric("Success Rate", perf_stats.get("success_rate", "0%"))
        with col3:
            st.metric("Avg Execution Time", perf_stats.get("average_execution_time", "0s"))
        with col4:
            st.metric("Active Queries", perf_stats.get("active_queries", 0))
        
        # System metrics
        st.subheader("💻 System Metrics")
        system_metrics = perf_stats.get("system_metrics", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Memory Usage", system_metrics.get("memory_usage", "0 MB"))
        with col2:
            st.metric("CPU Usage", system_metrics.get("cpu_usage", "0%"))
        with col3:
            st.metric("Disk Usage", system_metrics.get("disk_usage", "0%"))
        
        # Query trends
        query_trends = dashboard_data.get("query_trends", {})
        if query_trends and not query_trends.get("error"):
            st.subheader("📈 Query Trends (24h)")
            
            trends_data = query_trends.get("hourly_trends", [])
            if trends_data:
                df_trends = pd.DataFrame(trends_data)
                df_trends['hour'] = pd.to_datetime(df_trends['hour'])
                
                fig = px.line(
                    df_trends,
                    x='hour',
                    y='query_count',
                    title='Query Count Over Time',
                    labels={'query_count': 'Number of Queries', 'hour': 'Time'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Slow queries
        slow_queries = dashboard_data.get("slow_queries", [])
        if slow_queries:
            st.subheader("🐌 Slow Queries")
            df_slow = pd.DataFrame(slow_queries)
            st.dataframe(df_slow, use_container_width=True, hide_index=True)
        
        # Table usage
        table_usage = dashboard_data.get("table_usage", {})
        if table_usage.get("table_stats"):
            st.subheader("🗃️ Table Usage Statistics")
            df_tables = pd.DataFrame(table_usage["table_stats"])
            
            fig = px.bar(
                df_tables.head(10),
                x='table_name',
                y='usage_count',
                title='Most Used Database Tables'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_cache_management(self):
        """Render cache management interface"""
        st.header("🗄️ Cache Management")
        
        # Get cache stats
        cache_stats = self.make_api_request("/cache/stats")
        
        if cache_stats.get("error"):
            st.error("❌ Failed to load cache data")
            return
        
        # Cache metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cache Size", cache_stats.get("size", 0))
        with col2:
            st.metric("Hit Rate", cache_stats.get("hit_rate", "0%"))
        with col3:
            st.metric("Utilization", cache_stats.get("utilization", "0%"))
        with col4:
            st.metric("Evictions", cache_stats.get("evictions", 0))
        
        # Cache actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Cache", type="secondary"):
                result = self.make_api_request("/cache/clear", "DELETE")
                if not result.get("error"):
                    st.success("✅ Cache cleared successfully")
                    st.rerun()
                else:
                    st.error("❌ Failed to clear cache")
        
        with col2:
            if st.button("🔄 Refresh Stats"):
                st.rerun()
        
        # Top accessed entries
        top_accessed = self.make_api_request("/cache/top-accessed")
        if top_accessed and not top_accessed.get("error"):
            st.subheader("🔥 Most Accessed Cache Entries")
            df_cache = pd.DataFrame(top_accessed)
            st.dataframe(df_cache, use_container_width=True, hide_index=True)

def main():
    """Main application function"""
    app = QuickCommerceApp()
    
    # Render header
    app.render_header()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        
        # Check API health
        health = app.make_api_request("/health")
        if health.get("status") == "healthy":
            st.success("🟢 API Status: Healthy")
        else:
            st.error("🔴 API Status: Unhealthy")
        
        # Navigation menu
        page = st.selectbox(
            "Choose Page",
            [
                "🔍 Query Interface",
                "🔧 Advanced Search", 
                "📊 Monitoring",
                "🗄️ Cache Management"
            ]
        )
    
    # Render selected page
    if page == "🔍 Query Interface":
        app.render_query_interface()
    elif page == "🔧 Advanced Search":
        app.render_advanced_search()
    elif page == "📊 Monitoring":
        app.render_monitoring_dashboard()
    elif page == "🗄️ Cache Management":
        app.render_cache_management()

if __name__ == "__main__":
    main()
