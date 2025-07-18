from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database.models import Base
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.setup_database()
    
    def setup_database(self):
        """Initialize database connection with optimization settings"""
        try:
            # Create engine with connection pooling and optimization
            self.engine = create_engine(
                Config.DATABASE_URL,
                poolclass=StaticPool,
                pool_size=Config.DATABASE_POOL_SIZE,
                max_overflow=Config.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                    "isolation_level": None
                },
                echo=Config.LOG_LEVEL == "DEBUG"
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Execute SQLite optimizations
            self.optimize_sqlite()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def optimize_sqlite(self):
        """Apply SQLite performance optimizations"""
        optimizations = [
            "PRAGMA journal_mode = WAL;",
            "PRAGMA synchronous = NORMAL;",
            "PRAGMA cache_size = -64000;",  # 64MB cache
            "PRAGMA temp_store = MEMORY;",
            "PRAGMA mmap_size = 268435456;",  # 256MB mmap
            "PRAGMA optimize;",
            "PRAGMA analysis_limit = 1000;",
            "PRAGMA threads = 4;"
        ]
        
        with self.engine.connect() as conn:
            for pragma in optimizations:
                try:
                    conn.execute(text(pragma))
                    logger.debug(f"Applied optimization: {pragma}")
                except Exception as e:
                    logger.warning(f"Failed to apply optimization {pragma}: {e}")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_connection(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()

def get_db():
    """Dependency for FastAPI to get database session"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Get database session for direct use"""
    return db_manager.get_session()
