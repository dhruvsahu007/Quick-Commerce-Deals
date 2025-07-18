# Project Architecture Documentation

## Overview
Quick Commerce Deals is a sophisticated price comparison platform that uses AI-powered natural language processing to help users find the best deals across multiple quick commerce platforms.

## System Architecture

### 1. Database Layer (`database/`)
- **Models** (`models.py`): Comprehensive database schema with 25+ tables
- **Connection** (`connection.py`): Optimized database connection management
- **Initialization** (`init_db.py`): Sample data generation with realistic Indian market data

#### Key Tables:
- **Core Tables**: products, platforms, categories, brands
- **Pricing Tables**: product_prices, price_history, promotions
- **Analytics Tables**: product_popularity, market_trends, competitor_analysis
- **User Tables**: users, user_addresses, search_queries
- **Operational Tables**: inventory_levels, delivery_zones, platform_availability

### 2. AI Agent Layer (`agents/`)
- **Schema Analyzer** (`schema_analyzer.py`): Intelligent table selection and query planning
- **SQL Agent** (`sql_agent.py`): Natural language to SQL conversion using LangChain

#### Features:
- Semantic indexing for 50+ tables
- Query complexity analysis
- Optimal join path determination
- Multi-step query validation
- Fallback template-based SQL generation

### 3. Performance Layer
#### Caching (`cache/`)
- **Query Cache** (`query_cache.py`): LRU cache with TTL and statistics
- Result caching with metadata
- Schema information caching

#### Monitoring (`monitoring/`)
- **Performance Monitor** (`performance.py`): Real-time query performance tracking
- System resource monitoring
- Slow query detection
- Query trend analysis

### 4. API Layer (`api/`)
- **FastAPI Backend** (`main.py`): RESTful API with rate limiting
- Comprehensive error handling
- Security middleware
- OpenAPI documentation

#### Endpoints:
- `/query` - Natural language query processing
- `/popular-queries` - Sample queries
- `/cache/stats` - Cache management
- `/monitoring/dashboard` - Performance metrics
- `/platforms` - Platform information
- `/products/search` - Advanced product search

### 5. Web Interface (`web/`)
- **Streamlit App** (`app.py`): Interactive web interface
- Real-time data visualization
- Advanced search capabilities
- Monitoring dashboard
- Cache management interface

### 6. Data Simulation (`data/`)
- **Real-time Simulator** (`simulate_data.py`): Live price and inventory updates
- Market trend simulation
- Promotional offer management
- Competitive analysis generation

## Performance Optimizations

### Database Optimizations
1. **Indexing Strategy**:
   - Composite indexes on frequently joined columns
   - Covering indexes for common query patterns
   - Date-based indexes for time-series data

2. **SQLite Optimizations**:
   - WAL mode for concurrent access
   - Memory-mapped I/O
   - Query planner optimizations

3. **Connection Pooling**:
   - Configured pool size and overflow
   - Connection pre-ping for reliability

### Query Optimization
1. **Intelligent Table Selection**:
   - Semantic keyword matching
   - Query intent analysis
   - Cost-based table prioritization

2. **Query Planning**:
   - Optimal join order determination
   - Complexity scoring
   - Resource usage estimation

3. **Caching Strategy**:
   - Multi-level caching (query, result, schema)
   - LRU eviction with access patterns
   - TTL-based expiration

### API Performance
1. **Rate Limiting**:
   - Per-IP request throttling
   - Sliding window implementation
   - Graceful degradation

2. **Response Optimization**:
   - Result pagination
   - Selective field inclusion
   - Compression middleware

## Security Features

### API Security
1. **Rate Limiting**: Prevents abuse and ensures fair usage
2. **Input Validation**: Pydantic models for request validation
3. **Error Handling**: Secure error messages without information leakage
4. **CORS Configuration**: Configurable cross-origin policies

### SQL Injection Prevention
1. **Parameterized Queries**: All user inputs are properly parameterized
2. **Query Validation**: Multi-level validation before execution
3. **Template-based Fallback**: Safe fallback when LLM fails

## Scalability Considerations

### Horizontal Scaling
1. **Stateless Design**: All components are stateless for easy scaling
2. **Database Connection Pooling**: Efficient resource utilization
3. **Cache Distribution**: Ready for Redis clustering

### Vertical Scaling
1. **Memory Optimization**: Efficient data structures and caching
2. **CPU Optimization**: Async processing where applicable
3. **I/O Optimization**: Connection pooling and query optimization

## Monitoring and Observability

### Performance Metrics
1. **Query Performance**: Execution time, complexity, success rate
2. **System Metrics**: Memory, CPU, disk usage
3. **Cache Metrics**: Hit rate, eviction rate, utilization

### Analytics
1. **Usage Patterns**: Popular queries, table usage, user behavior
2. **Performance Trends**: Time-series analysis of system performance
3. **Error Analysis**: Failed query patterns and optimization opportunities

## Development Guidelines

### Code Organization
- Modular architecture with clear separation of concerns
- Comprehensive error handling and logging
- Type hints and documentation throughout

### Testing Strategy
- Unit tests for core logic
- Integration tests for API endpoints
- Performance tests for query optimization

### Deployment
- Docker containerization ready
- Environment-based configuration
- Health check endpoints for monitoring

## Future Enhancements

### Advanced Features
1. **Machine Learning**: Predictive pricing and demand forecasting
2. **Real-time Alerts**: Price drop notifications and deal alerts
3. **Recommendation Engine**: Personalized product recommendations
4. **Mobile App**: React Native or Flutter mobile application

### Infrastructure
1. **Microservices**: Break down into smaller, focused services
2. **Event Streaming**: Real-time data processing with Kafka
3. **Cloud Deployment**: AWS/Azure deployment with auto-scaling
4. **CDN Integration**: Global content delivery for faster response times
