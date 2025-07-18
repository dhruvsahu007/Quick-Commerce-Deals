from typing import Dict, Any, List, Optional
import time
import psutil
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    query_id: str
    sql_query: str
    start_time: float
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    success: bool = False
    result_count: int = 0
    error_message: Optional[str] = None
    complexity_score: int = 0
    tables_involved: List[str] = None
    memory_usage: float = 0
    cpu_usage: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PerformanceMonitor:
    """Monitor query performance and system metrics"""
    
    def __init__(self):
        self.active_queries: Dict[str, QueryMetrics] = {}
        self.completed_queries: List[QueryMetrics] = []
        self.max_history = 1000
        self.lock = threading.RLock()
        
        # Performance counters
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.total_execution_time = 0.0
        
        # Alert thresholds
        self.slow_query_threshold = 5.0  # seconds
        self.high_memory_threshold = 100  # MB
        
        # Start monitoring thread
        self._start_monitoring_thread()
    
    def start_query_monitoring(self, sql_query: str, query_plan=None) -> str:
        """Start monitoring a query execution"""
        query_id = f"query_{int(time.time() * 1000)}_{threading.get_ident()}"
        
        with self.lock:
            metrics = QueryMetrics(
                query_id=query_id,
                sql_query=sql_query,
                start_time=time.time(),
                complexity_score=getattr(query_plan, 'complexity_score', 0),
                tables_involved=getattr(query_plan, 'tables', []),
                memory_usage=self._get_memory_usage(),
                cpu_usage=self._get_cpu_usage()
            )
            
            self.active_queries[query_id] = metrics
            self.total_queries += 1
        
        logger.debug(f"Started monitoring query: {query_id}")
        return query_id
    
    def end_query_monitoring(self, query_id: str, success: bool, result_count: int = 0, error_message: str = None):
        """End monitoring for a query"""
        with self.lock:
            if query_id not in self.active_queries:
                logger.warning(f"Query ID not found in active queries: {query_id}")
                return
            
            metrics = self.active_queries.pop(query_id)
            metrics.end_time = time.time()
            metrics.execution_time = metrics.end_time - metrics.start_time
            metrics.success = success
            metrics.result_count = result_count
            metrics.error_message = error_message
            
            # Update counters
            if success:
                self.successful_queries += 1
            else:
                self.failed_queries += 1
            
            self.total_execution_time += metrics.execution_time
            
            # Check for performance alerts
            self._check_performance_alerts(metrics)
            
            # Store in history
            self.completed_queries.append(metrics)
            
            # Maintain history size
            if len(self.completed_queries) > self.max_history:
                self.completed_queries = self.completed_queries[-self.max_history:]
        
        logger.debug(f"Completed monitoring query: {query_id} (Success: {success}, Time: {metrics.execution_time:.3f}s)")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self.lock:
            if self.total_queries == 0:
                return {
                    'total_queries': 0,
                    'success_rate': 0,
                    'average_execution_time': 0,
                    'slow_queries_count': 0,
                    'active_queries': 0
                }
            
            recent_queries = [q for q in self.completed_queries if q.end_time and q.end_time > time.time() - 3600]
            slow_queries = [q for q in recent_queries if q.execution_time and q.execution_time > self.slow_query_threshold]
            
            return {
                'total_queries': self.total_queries,
                'successful_queries': self.successful_queries,
                'failed_queries': self.failed_queries,
                'success_rate': f"{(self.successful_queries / self.total_queries * 100):.2f}%",
                'average_execution_time': f"{(self.total_execution_time / self.total_queries):.3f}s",
                'slow_queries_count': len(slow_queries),
                'active_queries': len(self.active_queries),
                'recent_queries': len(recent_queries),
                'system_metrics': {
                    'memory_usage': f"{self._get_memory_usage():.2f} MB",
                    'cpu_usage': f"{self._get_cpu_usage():.2f}%",
                    'disk_usage': f"{self._get_disk_usage():.2f}%"
                }
            }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest queries"""
        with self.lock:
            slow_queries = sorted(
                [q for q in self.completed_queries if q.execution_time],
                key=lambda x: x.execution_time,
                reverse=True
            )
            
            return [
                {
                    'query_id': q.query_id,
                    'sql_query': q.sql_query[:100] + '...' if len(q.sql_query) > 100 else q.sql_query,
                    'execution_time': f"{q.execution_time:.3f}s",
                    'complexity_score': q.complexity_score,
                    'tables_involved': q.tables_involved,
                    'result_count': q.result_count,
                    'timestamp': datetime.fromtimestamp(q.start_time).isoformat()
                }
                for q in slow_queries[:limit]
            ]
    
    def get_failed_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failed queries"""
        with self.lock:
            failed_queries = sorted(
                [q for q in self.completed_queries if not q.success],
                key=lambda x: x.start_time,
                reverse=True
            )
            
            return [
                {
                    'query_id': q.query_id,
                    'sql_query': q.sql_query[:100] + '...' if len(q.sql_query) > 100 else q.sql_query,
                    'error_message': q.error_message,
                    'complexity_score': q.complexity_score,
                    'timestamp': datetime.fromtimestamp(q.start_time).isoformat()
                }
                for q in failed_queries[:limit]
            ]
    
    def get_query_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get query performance trends"""
        with self.lock:
            cutoff_time = time.time() - (hours * 3600)
            recent_queries = [q for q in self.completed_queries if q.start_time > cutoff_time]
            
            if not recent_queries:
                return {'error': 'No recent queries found'}
            
            # Group by hour
            hourly_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'failures': 0})
            
            for query in recent_queries:
                hour = datetime.fromtimestamp(query.start_time).replace(minute=0, second=0, microsecond=0)
                hourly_stats[hour]['count'] += 1
                if query.execution_time:
                    hourly_stats[hour]['total_time'] += query.execution_time
                if not query.success:
                    hourly_stats[hour]['failures'] += 1
            
            # Format for response
            trends = []
            for hour, stats in sorted(hourly_stats.items()):
                avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
                trends.append({
                    'hour': hour.isoformat(),
                    'query_count': stats['count'],
                    'average_time': f"{avg_time:.3f}s",
                    'failure_rate': f"{(stats['failures'] / stats['count'] * 100):.2f}%" if stats['count'] > 0 else "0%"
                })
            
            return {
                'period_hours': hours,
                'total_queries': len(recent_queries),
                'hourly_trends': trends
            }
    
    def get_table_usage_stats(self) -> Dict[str, Any]:
        """Get statistics on table usage patterns"""
        with self.lock:
            table_usage = defaultdict(int)
            table_performance = defaultdict(list)
            
            for query in self.completed_queries:
                if query.tables_involved:
                    for table in query.tables_involved:
                        table_usage[table] += 1
                        if query.execution_time:
                            table_performance[table].append(query.execution_time)
            
            stats = []
            for table, count in sorted(table_usage.items(), key=lambda x: x[1], reverse=True):
                avg_time = sum(table_performance[table]) / len(table_performance[table]) if table_performance[table] else 0
                stats.append({
                    'table_name': table,
                    'usage_count': count,
                    'average_query_time': f"{avg_time:.3f}s"
                })
            
            return {
                'total_tables': len(table_usage),
                'table_stats': stats
            }
    
    def _check_performance_alerts(self, metrics: QueryMetrics):
        """Check for performance alerts and log warnings"""
        if metrics.execution_time and metrics.execution_time > self.slow_query_threshold:
            logger.warning(f"Slow query detected: {metrics.query_id} took {metrics.execution_time:.3f}s")
        
        if metrics.memory_usage > self.high_memory_threshold:
            logger.warning(f"High memory usage during query: {metrics.query_id} used {metrics.memory_usage:.2f}MB")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            return psutil.disk_usage('/').percent
        except:
            return 0.0
    
    def _start_monitoring_thread(self):
        """Start background monitoring thread"""
        def monitoring_worker():
            while True:
                try:
                    time.sleep(60)  # Monitor every minute
                    self._cleanup_old_queries()
                except Exception as e:
                    logger.error(f"Monitoring thread error: {e}")
        
        monitor_thread = threading.Thread(target=monitoring_worker, daemon=True)
        monitor_thread.start()
        logger.info("Performance monitoring thread started")
    
    def _cleanup_old_queries(self):
        """Clean up old query records"""
        with self.lock:
            # Remove queries older than 24 hours from active queries (shouldn't happen, but safety)
            cutoff_time = time.time() - (24 * 3600)
            old_active_queries = [
                qid for qid, metrics in self.active_queries.items() 
                if metrics.start_time < cutoff_time
            ]
            
            for qid in old_active_queries:
                logger.warning(f"Removing stale active query: {qid}")
                del self.active_queries[qid]

class QueryMonitor:
    """Main query monitoring interface"""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
    
    def start_query_monitoring(self, sql_query: str, query_plan=None) -> str:
        return self.performance_monitor.start_query_monitoring(sql_query, query_plan)
    
    def end_query_monitoring(self, query_id: str, success: bool, result_count: int = 0, error_message: str = None):
        self.performance_monitor.end_query_monitoring(query_id, success, result_count, error_message)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        return {
            'performance_stats': self.performance_monitor.get_performance_stats(),
            'slow_queries': self.performance_monitor.get_slow_queries(5),
            'failed_queries': self.performance_monitor.get_failed_queries(5),
            'query_trends': self.performance_monitor.get_query_trends(24),
            'table_usage': self.performance_monitor.get_table_usage_stats()
        }

# Global monitor instance
query_monitor = QueryMonitor()
