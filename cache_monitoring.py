import time
import logging
import json
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger("fastapi-hasura")

# In-memory metrics storage (will reset on app restart)
# For production, consider using Redis to store these metrics
cache_metrics = {
    "hits": 0,
    "misses": 0,
    "total_saved_ms": 0,
    "queries": {},
    "hourly_stats": {},
    "last_reset": datetime.now().isoformat()
}

def track_cache_hit(query_name: str, saved_ms: float):
    """Track a cache hit and the time saved"""
    cache_metrics["hits"] += 1
    cache_metrics["total_saved_ms"] += saved_ms
    
    # Track per-query stats
    if query_name not in cache_metrics["queries"]:
        cache_metrics["queries"][query_name] = {
            "hits": 0, 
            "misses": 0, 
            "total_saved_ms": 0
        }
    
    cache_metrics["queries"][query_name]["hits"] += 1
    cache_metrics["queries"][query_name]["total_saved_ms"] += saved_ms
    
    # Add hourly stats
    current_hour = datetime.now().strftime("%Y-%m-%d:%H")
    if current_hour not in cache_metrics["hourly_stats"]:
        cache_metrics["hourly_stats"][current_hour] = {
            "hits": 0, 
            "misses": 0, 
            "total_saved_ms": 0
        }
    
    cache_metrics["hourly_stats"][current_hour]["hits"] += 1
    cache_metrics["hourly_stats"][current_hour]["total_saved_ms"] += saved_ms
    
    # Log every 100 hits
    if cache_metrics["hits"] % 100 == 0:
        logger.info(f"Cache hit rate: {get_hit_rate():.2f}%, Total saved: {cache_metrics['total_saved_ms']/1000:.2f}s")

def track_cache_miss(query_name: str):
    """Track a cache miss"""
    cache_metrics["misses"] += 1
    
    # Track per-query stats
    if query_name not in cache_metrics["queries"]:
        cache_metrics["queries"][query_name] = {
            "hits": 0, 
            "misses": 0, 
            "total_saved_ms": 0
        }
    
    cache_metrics["queries"][query_name]["misses"] += 1
    
    # Add hourly stats
    current_hour = datetime.now().strftime("%Y-%m-%d:%H")
    if current_hour not in cache_metrics["hourly_stats"]:
        cache_metrics["hourly_stats"][current_hour] = {
            "hits": 0, 
            "misses": 0, 
            "total_saved_ms": 0
        }
    
    cache_metrics["hourly_stats"][current_hour]["misses"] += 1

def get_hit_rate() -> float:
    """Calculate the cache hit rate"""
    total = cache_metrics["hits"] + cache_metrics["misses"]
    if total == 0:
        return 0
    return (cache_metrics["hits"] / total) * 100

def get_query_stats(query_name: Optional[str] = None) -> Dict[str, Any]:
    """Get statistics for all queries or a specific query"""
    if query_name:
        return cache_metrics["queries"].get(query_name, {
            "hits": 0, 
            "misses": 0, 
            "total_saved_ms": 0,
            "hit_rate": 0
        })
    
    return cache_metrics["queries"]

def get_hourly_stats() -> Dict[str, Any]:
    """Get hourly cache statistics"""
    return cache_metrics["hourly_stats"]

def reset_metrics():
    """Reset all cache metrics"""
    global cache_metrics
    cache_metrics = {
        "hits": 0,
        "misses": 0,
        "total_saved_ms": 0,
        "queries": {},
        "hourly_stats": {},
        "last_reset": datetime.now().isoformat()
    }
    logger.info("Cache metrics reset")

def get_summary() -> Dict[str, Any]:
    """Get a summary of cache metrics"""
    total = cache_metrics["hits"] + cache_metrics["misses"]
    hit_rate = get_hit_rate()
    
    # Calculate average time saved per hit
    avg_time_saved = 0
    if cache_metrics["hits"] > 0:
        avg_time_saved = cache_metrics["total_saved_ms"] / cache_metrics["hits"]
    
    # Find top 5 most efficient cached queries
    query_stats = []
    for name, stats in cache_metrics["queries"].items():
        total_query = stats["hits"] + stats["misses"]
        hit_rate_query = 0
        if total_query > 0:
            hit_rate_query = (stats["hits"] / total_query) * 100
        
        avg_time_saved_query = 0
        if stats["hits"] > 0:
            avg_time_saved_query = stats["total_saved_ms"] / stats["hits"]
        
        query_stats.append({
            "name": name,
            "hit_rate": hit_rate_query,
            "avg_time_saved_ms": avg_time_saved_query,
            "total_hits": stats["hits"],
            "total_misses": stats["misses"]
        })
    
    # Sort by time saved
    query_stats.sort(key=lambda x: x["avg_time_saved_ms"], reverse=True)
    top_queries = query_stats[:5]
    
    # Cleanup old hourly stats (keep last 24 hours)
    now = datetime.now()
    cutoff = (now - timedelta(hours=24)).strftime("%Y-%m-%d:%H")
    
    hourly_stats = {}
    for hour, stats in cache_metrics["hourly_stats"].items():
        if hour >= cutoff:
            hourly_stats[hour] = stats
    
    cache_metrics["hourly_stats"] = hourly_stats
    
    return {
        "total_requests": total,
        "hits": cache_metrics["hits"],
        "misses": cache_metrics["misses"],
        "hit_rate": hit_rate,
        "total_saved_ms": cache_metrics["total_saved_ms"],
        "avg_time_saved_ms": avg_time_saved,
        "top_queries": top_queries,
        "since": cache_metrics["last_reset"]
    }

def cache_decorator(query_name: str):
    """Decorator to automatically track cache metrics for a function"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result, from_cache = await func(*args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if from_cache:
                # If from cache, we estimate time saved based on average non-cached execution time
                saved_ms = elapsed_ms * 5  # Assuming cache is 5x faster on average
                track_cache_hit(query_name, saved_ms)
            else:
                track_cache_miss(query_name)
            
            return result
        
        return wrapper
    
    return decorator 