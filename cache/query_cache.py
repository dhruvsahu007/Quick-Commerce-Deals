from typing import Any, Dict, Optional
import hashlib
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import OrderedDict
import threading
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    data: Any
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime = None
    ttl: int = Config.CACHE_TTL
    
    def is_expired(self) -> bool:
        return datetime.utcnow() - self.created_at > timedelta(seconds=self.ttl)
    
    def access(self):
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

class QueryCache:
    """Advanced query caching with TTL, LRU eviction, and statistics"""
    
    def __init__(self, max_size: int = Config.CACHE_MAX_SIZE):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0
        }
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def generate_cache_key(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate cache key from query and context"""
        cache_input = {
            'query': query.lower().strip(),
            'context': context or {}
        }
        
        # Create hash of the input
        cache_str = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check if expired
                if entry.is_expired():
                    del self.cache[key]
                    self.stats['misses'] += 1
                    self.stats['size'] = len(self.cache)
                    return None
                
                # Access the entry (updates LRU)
                entry.access()
                self.cache.move_to_end(key)
                self.stats['hits'] += 1
                
                logger.debug(f"Cache hit for key: {key[:16]}...")
                return entry.data
            
            self.stats['misses'] += 1
            logger.debug(f"Cache miss for key: {key[:16]}...")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set item in cache"""
        with self.lock:
            # Check if we need to evict
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            # Create cache entry
            entry = CacheEntry(
                data=value,
                created_at=datetime.utcnow(),
                ttl=ttl or Config.CACHE_TTL
            )
            
            self.cache[key] = entry
            self.cache.move_to_end(key)
            self.stats['size'] = len(self.cache)
            
            logger.debug(f"Cached result for key: {key[:16]}...")
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if self.cache:
            evicted_key, _ = self.cache.popitem(last=False)
            self.stats['evictions'] += 1
            logger.debug(f"Evicted LRU item: {evicted_key[:16]}...")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.stats['size'] = 0
            logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries"""
        with self.lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            self.stats['size'] = len(self.cache)
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': self.stats['size'],
                'max_size': self.max_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'hit_rate': f"{hit_rate:.2f}%",
                'evictions': self.stats['evictions'],
                'utilization': f"{(self.stats['size'] / self.max_size * 100):.2f}%"
            }
    
    def get_top_accessed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most accessed cache entries"""
        with self.lock:
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].access_count,
                reverse=True
            )
            
            return [
                {
                    'key': key[:16] + '...',
                    'access_count': entry.access_count,
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat() if entry.last_accessed else None
                }
                for key, entry in sorted_entries[:limit]
            ]
    
    def _start_cleanup_thread(self):
        """Start background thread for periodic cleanup"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Cleanup every 5 minutes
                    self.cleanup_expired()
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Cache cleanup thread started")

class ResultCache:
    """Specialized cache for formatted query results"""
    
    def __init__(self):
        self.query_cache = QueryCache()
    
    def cache_result(self, query: str, result: Dict[str, Any], context: Dict[str, Any] = None):
        """Cache query result with metadata"""
        cache_data = {
            'result': result,
            'cached_at': datetime.utcnow().isoformat(),
            'query': query,
            'context': context
        }
        
        key = self.query_cache.generate_cache_key(query, context)
        self.query_cache.set(key, cache_data)
    
    def get_cached_result(self, query: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Get cached result for query"""
        key = self.query_cache.generate_cache_key(query, context)
        cached_data = self.query_cache.get(key)
        
        if cached_data:
            # Add cache metadata to result
            result = cached_data['result'].copy()
            result['metadata']['cached'] = True
            result['metadata']['cached_at'] = cached_data['cached_at']
            return result
        
        return None

class SchemaCache:
    """Cache for database schema information"""
    
    def __init__(self):
        self.cache = {}
        self.last_updated = None
        self.ttl = 3600  # 1 hour TTL for schema cache
    
    def get_schema_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get cached schema information for table"""
        if self.is_expired():
            return None
        
        return self.cache.get(table_name)
    
    def set_schema_info(self, table_name: str, schema_info: Dict[str, Any]):
        """Cache schema information for table"""
        self.cache[table_name] = schema_info
        self.last_updated = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if schema cache is expired"""
        if not self.last_updated:
            return True
        
        return datetime.utcnow() - self.last_updated > timedelta(seconds=self.ttl)
    
    def invalidate(self):
        """Invalidate schema cache"""
        self.cache.clear()
        self.last_updated = None

# Global cache instances
query_cache = QueryCache()
result_cache = ResultCache() 
schema_cache = SchemaCache()
