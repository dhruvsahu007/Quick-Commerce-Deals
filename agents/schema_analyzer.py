from typing import List, Dict, Any, Optional, Tuple
import re
import json
import time
from dataclasses import dataclass
from sqlalchemy import text, inspect
from database.connection import get_db_session
from database.models import *
from cache.query_cache import QueryCache
from monitoring.performance import QueryMonitor
import logging

logger = logging.getLogger(__name__)

@dataclass
class TableInfo:
    name: str
    columns: List[str]
    relationships: Dict[str, str]
    description: str
    size_estimate: int

@dataclass
class QueryPlan:
    tables: List[str]
    joins: List[str]
    conditions: List[str]
    complexity_score: int
    estimated_cost: float

class SchemaAnalyzer:
    """Analyzes database schema and provides intelligent table selection"""
    
    def __init__(self):
        self.db = get_db_session()
        self.tables_info = {}
        self.semantic_index = {}
        self._build_schema_cache()
    
    def _build_schema_cache(self):
        """Build comprehensive schema cache with semantic indexing"""
        try:
            inspector = inspect(self.db.bind)
            
            # Core table definitions with semantic meaning
            table_definitions = {
                'products': {
                    'description': 'Product catalog with names, descriptions, categories, brands',
                    'keywords': ['product', 'item', 'goods', 'merchandise', 'name', 'brand', 'category'],
                    'relationships': {
                        'category_id': 'categories.id',
                        'brand_id': 'brands.id'
                    }
                },
                'product_prices': {
                    'description': 'Current pricing across platforms with discounts and availability',
                    'keywords': ['price', 'cost', 'rate', 'cheap', 'expensive', 'discount', 'offer', 'deal'],
                    'relationships': {
                        'product_id': 'products.id',
                        'platform_id': 'platforms.id'
                    }
                },
                'platforms': {
                    'description': 'Quick commerce platforms like Blinkit, Zepto, Instamart',
                    'keywords': ['platform', 'app', 'store', 'blinkit', 'zepto', 'instamart', 'bigbasket'],
                    'relationships': {}
                },
                'categories': {
                    'description': 'Product categories and subcategories hierarchically organized',
                    'keywords': ['category', 'type', 'kind', 'fruits', 'vegetables', 'dairy', 'snacks'],
                    'relationships': {
                        'parent_id': 'categories.id'
                    }
                },
                'brands': {
                    'description': 'Product brands and manufacturers',
                    'keywords': ['brand', 'manufacturer', 'company', 'make'],
                    'relationships': {}
                },
                'promotions': {
                    'description': 'Active promotional offers and discounts',
                    'keywords': ['promotion', 'offer', 'deal', 'discount', 'sale', 'coupon'],
                    'relationships': {
                        'platform_id': 'platforms.id'
                    }
                },
                'price_history': {
                    'description': 'Historical price changes and trends',
                    'keywords': ['history', 'trend', 'change', 'historical', 'past', 'previous'],
                    'relationships': {
                        'product_price_id': 'product_prices.id'
                    }
                },
                'inventory_levels': {
                    'description': 'Stock availability and inventory status',
                    'keywords': ['stock', 'inventory', 'available', 'quantity', 'out of stock'],
                    'relationships': {
                        'product_id': 'products.id',
                        'platform_id': 'platforms.id'
                    }
                },
                'product_popularity': {
                    'description': 'Product popularity metrics and search trends',
                    'keywords': ['popular', 'trending', 'bestseller', 'views', 'searches'],
                    'relationships': {
                        'product_id': 'products.id',
                        'platform_id': 'platforms.id'
                    }
                },
                'competitor_analysis': {
                    'description': 'Price comparison between platforms for same products',
                    'keywords': ['compare', 'comparison', 'versus', 'vs', 'between', 'difference'],
                    'relationships': {
                        'product_id': 'products.id'
                    }
                },
                'delivery_zones': {
                    'description': 'Delivery areas and zones for each platform',
                    'keywords': ['delivery', 'zone', 'area', 'location', 'pincode', 'city'],
                    'relationships': {
                        'platform_id': 'platforms.id'
                    }
                },
                'market_trends': {
                    'description': 'Market analysis and pricing trends by category',
                    'keywords': ['trend', 'market', 'analysis', 'growth', 'decline'],
                    'relationships': {
                        'category_id': 'categories.id',
                        'platform_id': 'platforms.id'
                    }
                },
                'product_reviews': {
                    'description': 'User reviews and ratings for products',
                    'keywords': ['review', 'rating', 'feedback', 'comment', 'opinion'],
                    'relationships': {
                        'product_id': 'products.id',
                        'platform_id': 'platforms.id'
                    }
                },
                'platform_ratings': {
                    'description': 'Overall platform ratings and user feedback',
                    'keywords': ['platform rating', 'app rating', 'service rating'],
                    'relationships': {
                        'platform_id': 'platforms.id'
                    }
                }
            }
            
            for table_name in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                table_def = table_definitions.get(table_name, {})
                
                self.tables_info[table_name] = TableInfo(
                    name=table_name,
                    columns=columns,
                    relationships=table_def.get('relationships', {}),
                    description=table_def.get('description', f'Table: {table_name}'),
                    size_estimate=self._estimate_table_size(table_name)
                )
                
                # Build semantic index
                keywords = table_def.get('keywords', [])
                for keyword in keywords:
                    if keyword not in self.semantic_index:
                        self.semantic_index[keyword] = []
                    self.semantic_index[keyword].append(table_name)
            
            logger.info(f"Schema cache built with {len(self.tables_info)} tables")
            
        except Exception as e:
            logger.error(f"Failed to build schema cache: {e}")
            raise
        finally:
            self.db.close()
    
    def _estimate_table_size(self, table_name: str) -> int:
        """Estimate table size for query optimization"""
        try:
            result = self.db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            return result or 0
        except:
            return 1000  # Default estimate
    
    def find_relevant_tables(self, query: str) -> List[str]:
        """Find relevant tables based on semantic analysis of query"""
        query_lower = query.lower()
        relevant_tables = set()
        
        # Direct keyword matching
        for keyword, tables in self.semantic_index.items():
            if keyword in query_lower:
                relevant_tables.update(tables)
        
        # Entity-specific matching
        platform_names = ['blinkit', 'zepto', 'instamart', 'bigbasket', 'dunzo', 'swiggy', 'amazon', 'flipkart']
        if any(platform in query_lower for platform in platform_names):
            relevant_tables.add('platforms')
            relevant_tables.add('product_prices')
        
        # Query intent analysis
        if any(word in query_lower for word in ['cheapest', 'lowest', 'minimum', 'best price']):
            relevant_tables.update(['product_prices', 'products', 'platforms'])
        
        if any(word in query_lower for word in ['discount', 'offer', 'deal', '%']):
            relevant_tables.update(['product_prices', 'promotions', 'products'])
        
        if any(word in query_lower for word in ['compare', 'comparison', 'between', 'vs']):
            relevant_tables.update(['competitor_analysis', 'product_prices', 'platforms'])
        
        if any(word in query_lower for word in ['available', 'stock', 'in stock']):
            relevant_tables.update(['inventory_levels', 'product_prices', 'products'])
        
        # Ensure minimum required tables
        if not relevant_tables:
            relevant_tables = {'products', 'product_prices', 'platforms'}
        
        return list(relevant_tables)
    
    def get_optimal_join_path(self, tables: List[str]) -> List[str]:
        """Determine optimal join path between tables"""
        if len(tables) <= 1:
            return []
        
        joins = []
        connected_tables = {tables[0]}
        remaining_tables = set(tables[1:])
        
        while remaining_tables:
            best_join = None
            best_cost = float('inf')
            
            for connected_table in connected_tables:
                for remaining_table in remaining_tables:
                    join_info = self._find_join_relationship(connected_table, remaining_table)
                    if join_info:
                        cost = self._calculate_join_cost(connected_table, remaining_table)
                        if cost < best_cost:
                            best_cost = cost
                            best_join = (connected_table, remaining_table, join_info)
            
            if best_join:
                connected_table, remaining_table, join_info = best_join
                joins.append(join_info)
                connected_tables.add(remaining_table)
                remaining_tables.remove(remaining_table)
            else:
                # Force join if no relationship found
                remaining_table = remaining_tables.pop()
                joins.append(f"-- No direct relationship found for {remaining_table}")
                connected_tables.add(remaining_table)
        
        return joins
    
    def _find_join_relationship(self, table1: str, table2: str) -> Optional[str]:
        """Find join relationship between two tables"""
        table1_info = self.tables_info.get(table1)
        table2_info = self.tables_info.get(table2)
        
        if not table1_info or not table2_info:
            return None
        
        # Check direct relationships
        for col, rel in table1_info.relationships.items():
            if rel.startswith(f"{table2}."):
                return f"{table1}.{col} = {rel}"
        
        for col, rel in table2_info.relationships.items():
            if rel.startswith(f"{table1}."):
                return f"{table2}.{col} = {rel}"
        
        # Common join patterns
        common_joins = {
            ('products', 'product_prices'): 'products.id = product_prices.product_id',
            ('products', 'categories'): 'products.category_id = categories.id',
            ('products', 'brands'): 'products.brand_id = brands.id',
            ('product_prices', 'platforms'): 'product_prices.platform_id = platforms.id',
            ('promotions', 'platforms'): 'promotions.platform_id = platforms.id',
            ('inventory_levels', 'products'): 'inventory_levels.product_id = products.id',
            ('inventory_levels', 'platforms'): 'inventory_levels.platform_id = platforms.id',
            ('price_history', 'product_prices'): 'price_history.product_price_id = product_prices.id',
            ('competitor_analysis', 'products'): 'competitor_analysis.product_id = products.id',
            ('product_popularity', 'products'): 'product_popularity.product_id = products.id',
            ('product_popularity', 'platforms'): 'product_popularity.platform_id = platforms.id'
        }
        
        return common_joins.get((table1, table2)) or common_joins.get((table2, table1))
    
    def _calculate_join_cost(self, table1: str, table2: str) -> float:
        """Calculate estimated cost of joining two tables"""
        size1 = self.tables_info[table1].size_estimate
        size2 = self.tables_info[table2].size_estimate
        return size1 * size2  # Simplified cost model
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get columns for a specific table"""
        return self.tables_info.get(table_name, TableInfo("", [], {}, "", 0)).columns

class QueryPlanner:
    """Plans and optimizes SQL queries based on natural language input"""
    
    def __init__(self):
        self.schema_analyzer = SchemaAnalyzer()
        self.cache = QueryCache()
        self.monitor = QueryMonitor()
    
    def analyze_query_complexity(self, query: str) -> int:
        """Analyze and score query complexity"""
        complexity = 0
        
        # Count operations
        complexity += len(re.findall(r'\bJOIN\b', query, re.IGNORECASE)) * 2
        complexity += len(re.findall(r'\bWHERE\b', query, re.IGNORECASE))
        complexity += len(re.findall(r'\bGROUP BY\b', query, re.IGNORECASE)) * 3
        complexity += len(re.findall(r'\bORDER BY\b', query, re.IGNORECASE))
        complexity += len(re.findall(r'\bHAVING\b', query, re.IGNORECASE)) * 2
        complexity += len(re.findall(r'\bSUBQUERY\b', query, re.IGNORECASE)) * 4
        
        return complexity
    
    def create_query_plan(self, natural_query: str) -> QueryPlan:
        """Create optimized query plan from natural language"""
        
        # Find relevant tables
        relevant_tables = self.schema_analyzer.find_relevant_tables(natural_query)
        
        # Get optimal join path
        joins = self.schema_analyzer.get_optimal_join_path(relevant_tables)
        
        # Generate conditions based on query analysis
        conditions = self._extract_conditions(natural_query)
        
        # Calculate complexity and cost
        complexity = len(relevant_tables) + len(joins) + len(conditions)
        estimated_cost = sum(
            self.schema_analyzer.tables_info[table].size_estimate 
            for table in relevant_tables
        )
        
        return QueryPlan(
            tables=relevant_tables,
            joins=joins,
            conditions=conditions,
            complexity_score=complexity,
            estimated_cost=estimated_cost
        )
    
    def _extract_conditions(self, query: str) -> List[str]:
        """Extract conditions from natural language query"""
        conditions = []
        query_lower = query.lower()
        
        # Price-related conditions
        if 'cheapest' in query_lower or 'lowest price' in query_lower:
            conditions.append("ORDER BY product_prices.current_price ASC")
        
        if 'most expensive' in query_lower or 'highest price' in query_lower:
            conditions.append("ORDER BY product_prices.current_price DESC")
        
        # Discount conditions
        discount_match = re.search(r'(\d+)%\s*(?:off|discount)', query_lower)
        if discount_match:
            percentage = discount_match.group(1)
            conditions.append(f"product_prices.discount_percentage >= {percentage}")
        
        # Platform conditions
        platform_names = {
            'blinkit': 'blinkit',
            'zepto': 'zepto', 
            'instamart': 'instamart',
            'bigbasket': 'bigbasket_now',
            'dunzo': 'dunzo',
            'swiggy': 'swiggy_genie',
            'amazon': 'amazon_fresh'
        }
        
        for platform_mention, platform_code in platform_names.items():
            if platform_mention in query_lower:
                conditions.append(f"platforms.name = '{platform_code}'")
        
        # Product-specific conditions
        product_keywords = {
            'onion': 'onion',
            'apple': 'apple', 
            'milk': 'milk',
            'banana': 'banana',
            'tomato': 'tomato',
            'potato': 'potato',
            'rice': 'rice',
            'bread': 'bread'
        }
        
        for keyword, product in product_keywords.items():
            if keyword in query_lower:
                conditions.append(f"LOWER(products.name) LIKE '%{product}%'")
        
        # Category conditions
        category_keywords = {
            'fruit': 'fresh_fruits',
            'fruits': 'fresh_fruits',
            'vegetable': 'fresh_vegetables', 
            'vegetables': 'fresh_vegetables',
            'dairy': 'dairy',
            'snack': 'snacks',
            'snacks': 'snacks'
        }
        
        for keyword, category in category_keywords.items():
            if keyword in query_lower:
                conditions.append(f"categories.name LIKE '%{category}%'")
        
        # Availability conditions
        if 'available' in query_lower or 'in stock' in query_lower:
            conditions.append("product_prices.is_available = 1")
            conditions.append("inventory_levels.stock_status != 'out_of_stock'")
        
        # Budget conditions
        budget_match = re.search(r'(?:under|below|less than|₹|rs\.?)\s*(\d+)', query_lower)
        if budget_match:
            amount = budget_match.group(1)
            conditions.append(f"product_prices.current_price <= {amount}")
        
        budget_match = re.search(r'(\d+)\s*(?:rupee|rs|₹)\s*(?:budget|limit)', query_lower)
        if budget_match:
            amount = budget_match.group(1)
            conditions.append(f"product_prices.current_price <= {amount}")
        
        return conditions
    
    def validate_query_plan(self, plan: QueryPlan) -> Tuple[bool, List[str]]:
        """Validate query plan and return issues if any"""
        issues = []
        
        # Check complexity
        if plan.complexity_score > 15:
            issues.append("Query complexity too high - consider simplifying")
        
        # Check table count
        if len(plan.tables) > 8:
            issues.append("Too many tables involved - may impact performance")
        
        # Check estimated cost
        if plan.estimated_cost > 1000000:
            issues.append("High estimated query cost - consider adding filters")
        
        # Check for required tables
        if 'products' not in plan.tables and any('product' in t for t in plan.tables):
            issues.append("Missing products table - may need to include it")
        
        return len(issues) == 0, issues
