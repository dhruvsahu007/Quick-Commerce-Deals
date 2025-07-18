from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import asyncio
from datetime import datetime
import logging

from agents.sql_agent import AdvancedSQLAgent
from cache.query_cache import query_cache, result_cache
from monitoring.performance import query_monitor
from database.connection import get_db
from config.settings import Config

# Setup logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Quick Commerce Deals API",
    description="Advanced price comparison platform for quick commerce apps",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Rate limiting storage
request_counts = {}
request_windows = {}

# Initialize SQL Agent
sql_agent = AdvancedSQLAgent()

# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query", min_length=3, max_length=500)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the query")
    use_cache: bool = Field(default=True, description="Whether to use cached results")

class QueryResponse(BaseModel):
    success: bool
    query: str
    sql_query: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    execution_time: float
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None
    plan: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    database_status: str
    cache_stats: Dict[str, Any]
    performance_stats: Dict[str, Any]

# Rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    
    # Initialize client if not exists
    if client_ip not in request_counts:
        request_counts[client_ip] = 0
        request_windows[client_ip] = current_time
    
    # Reset window if expired
    if current_time - request_windows[client_ip] > Config.RATE_LIMIT_WINDOW:
        request_counts[client_ip] = 0
        request_windows[client_ip] = current_time
    
    # Check rate limit
    if request_counts[client_ip] >= Config.RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Maximum {Config.RATE_LIMIT_REQUESTS} requests per {Config.RATE_LIMIT_WINDOW} seconds",
                "retry_after": Config.RATE_LIMIT_WINDOW - (current_time - request_windows[client_ip])
            }
        )
    
    # Increment request count
    request_counts[client_ip] += 1
    
    response = await call_next(request)
    return response

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Quick Commerce Deals API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check(db = Depends(get_db)):
    """Health check endpoint with system status"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    return HealthResponse(
        status="healthy" if database_status == "healthy" else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        database_status=database_status,
        cache_stats=query_cache.get_stats(),
        performance_stats=query_monitor.get_dashboard_data()['performance_stats']
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, client_request: Request):
    """Process natural language query and return results"""
    start_time = time.time()
    
    try:
        logger.info(f"Processing query from {client_request.client.host}: {request.query}")
        
        # Check cache first if enabled
        if request.use_cache:
            cached_result = result_cache.get_cached_result(request.query, request.context)
            if cached_result:
                logger.info("Returning cached result")
                return QueryResponse(**cached_result)
        
        # Process query with SQL agent
        result = sql_agent.process_natural_query(request.query, request.context)
        
        # Cache successful results
        if result['success'] and request.use_cache:
            result_cache.cache_result(request.query, result, request.context)
        
        # Convert to response model
        response = QueryResponse(
            success=result['success'],
            query=result['query'],
            sql_query=result.get('sql_query'),
            results=result.get('results'),
            execution_time=result.get('execution_time', time.time() - start_time),
            error=result.get('error'),
            suggestions=result.get('suggestions'),
            plan=result.get('plan'),
            metadata=result.get('metadata')
        )
        
        logger.info(f"Query processed successfully in {response.execution_time:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return QueryResponse(
            success=False,
            query=request.query,
            execution_time=time.time() - start_time,
            error=str(e),
            suggestions=["Please try a simpler query", "Check your query syntax"]
        )

@app.get("/popular-queries", response_model=List[str])
async def get_popular_queries():
    """Get list of popular/sample queries"""
    return sql_agent.get_popular_queries()

@app.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats():
    """Get cache statistics"""
    return query_cache.get_stats()

@app.get("/cache/top-accessed", response_model=List[Dict[str, Any]])
async def get_top_accessed_cache():
    """Get most accessed cache entries"""
    return query_cache.get_top_accessed()

@app.delete("/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    query_cache.clear()
    return {"message": "Cache cleared successfully"}

@app.get("/monitoring/dashboard", response_model=Dict[str, Any])
async def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data"""
    return query_monitor.get_dashboard_data()

@app.get("/monitoring/slow-queries", response_model=List[Dict[str, Any]])
async def get_slow_queries(limit: int = 10):
    """Get slowest queries"""
    return query_monitor.performance_monitor.get_slow_queries(limit)

@app.get("/monitoring/failed-queries", response_model=List[Dict[str, Any]])
async def get_failed_queries(limit: int = 10):
    """Get recent failed queries"""
    return query_monitor.performance_monitor.get_failed_queries(limit)

@app.get("/platforms", response_model=List[Dict[str, Any]])
async def get_platforms(db = Depends(get_db)):
    """Get list of available platforms"""
    try:
        from database.models import Platform
        platforms = db.query(Platform).filter(Platform.is_active == True).all()
        return [
            {
                "id": platform.id,
                "name": platform.name,
                "display_name": platform.display_name,
                "average_delivery_time": platform.average_delivery_time,
                "minimum_order_value": platform.minimum_order_value,
                "delivery_fee": platform.delivery_fee
            }
            for platform in platforms
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories", response_model=List[Dict[str, Any]])
async def get_categories(db = Depends(get_db)):
    """Get list of product categories"""
    try:
        from database.models import Category
        categories = db.query(Category).filter(Category.is_active == True).all()
        return [
            {
                "id": category.id,
                "name": category.name,
                "display_name": category.display_name,
                "level": category.level,
                "parent_id": category.parent_id
            }
            for category in categories
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/search", response_model=List[Dict[str, Any]])
async def search_products(
    q: str = "",
    category_id: Optional[int] = None,
    platform_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 20,
    db = Depends(get_db)
):
    """Search products with filters"""
    try:
        from database.models import Product, ProductPrice, Platform, Category
        from sqlalchemy import and_, or_
        
        query = db.query(
            Product.name.label('product_name'),
            Platform.display_name.label('platform'),
            ProductPrice.current_price,
            ProductPrice.original_price,
            ProductPrice.discount_percentage,
            ProductPrice.is_available
        ).join(
            ProductPrice, Product.id == ProductPrice.product_id
        ).join(
            Platform, ProductPrice.platform_id == Platform.id
        )
        
        # Apply filters
        filters = [ProductPrice.is_available == True]
        
        if q:
            filters.append(Product.name.ilike(f"%{q}%"))
        
        if category_id:
            filters.append(Product.category_id == category_id)
        
        if platform_id:
            filters.append(Platform.id == platform_id)
        
        if min_price is not None:
            filters.append(ProductPrice.current_price >= min_price)
        
        if max_price is not None:
            filters.append(ProductPrice.current_price <= max_price)
        
        query = query.filter(and_(*filters))
        query = query.order_by(ProductPrice.current_price)
        query = query.limit(limit)
        
        results = query.all()
        
        return [
            {
                "product_name": result.product_name,
                "platform": result.platform,
                "current_price": f"₹{result.current_price:.2f}",
                "original_price": f"₹{result.original_price:.2f}",
                "discount_percentage": f"{result.discount_percentage:.1f}%",
                "is_available": "Available" if result.is_available else "Out of Stock"
            }
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Quick Commerce Deals API starting up...")
    logger.info("SQL Agent initialized")
    logger.info("Cache system ready")
    logger.info("Monitoring system active")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Quick Commerce Deals API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.API_RELOAD,
        log_level=Config.LOG_LEVEL.lower()
    )
