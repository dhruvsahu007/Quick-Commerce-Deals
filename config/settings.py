import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DATABASE_URL = "sqlite:///./quick_commerce.db"
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 30
    
    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    API_RELOAD = True
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
    
    # Cache Configuration
    CACHE_TTL = 300  # 5 minutes
    CACHE_MAX_SIZE = 10000
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Data Simulation
    SIMULATION_INTERVAL = 30  # seconds
    PLATFORMS = [
        "Blinkit", "Zepto", "Instamart", "BigBasket Now", 
        "Dunzo", "Swiggy Genie", "Amazon Fresh", "Flipkart Quick",
        "JioMart Express", "Grofers"
    ]
    
    # Query Optimization
    MAX_QUERY_COMPLEXITY = 10
    QUERY_TIMEOUT = 30  # seconds
    MAX_RESULT_SIZE = 1000
    
    # Monitoring
    ENABLE_MONITORING = True
    LOG_LEVEL = "INFO"
