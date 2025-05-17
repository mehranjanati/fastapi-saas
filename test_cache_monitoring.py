"""
Test script for cache monitoring functionality.
"""
import asyncio
import json
import logging
import time
import random
from datetime import datetime

import cache_monitoring

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cache-monitor-test")

# Mock Redis cache - this simulates the cache operations for testing purposes
class MockCache:
    def __init__(self):
        self.cache = {}
        
    def get(self, key):
        if key in self.cache:
            # Simulate random cache hits
            if random.random() < 0.8:  # 80% cache hit rate
                return self.cache[key]
        return None
        
    def set(self, key, value, ttl=3600):
        self.cache[key] = value

# Simulate a GraphQL query
async def simulate_query(query_name, cache, variables=None):
    # Generate a cache key
    key = f"{query_name}:{json.dumps(variables or {})}"
    
    # Start timing
    start_time = time.time()
    
    # Check cache
    cached_result = cache.get(key)
    
    if cached_result:
        # Cache hit
        elapsed_time = (time.time() - start_time) * 1000  # ms
        estimated_saved = random.uniform(80, 150)  # Assume 80-150ms saved
        cache_monitoring.track_cache_hit(query_name, estimated_saved)
        logger.info(f"Cache HIT for {query_name} - Saved ~{estimated_saved:.2f}ms")
        return json.loads(cached_result)
    
    # Cache miss - simulate a database query
    cache_monitoring.track_cache_miss(query_name)
    logger.info(f"Cache MISS for {query_name}")
    
    # Simulate query execution time (50-200ms)
    await asyncio.sleep(random.uniform(0.05, 0.2))
    
    # Generate a mock result
    result = {
        "data": {
            "timestamp": datetime.now().isoformat(),
            "query": query_name,
            "variables": variables
        }
    }
    
    # Store in cache
    cache.set(key, json.dumps(result))
    
    return result

async def run_simulation():
    logger.info("Starting cache monitoring simulation")
    
    # Create a mock cache
    mock_cache = MockCache()
    
    # Simulate different query types
    query_types = [
        "get_users", 
        "get_products", 
        "get_orders", 
        "get_inventory",
        "get_analytics"
    ]
    
    # Run a series of simulated queries
    for _ in range(100):
        # Pick a random query type
        query_name = random.choice(query_types)
        
        # Generate random variables
        variables = {"limit": random.randint(10, 50)}
        
        # Simulate the query
        await simulate_query(query_name, mock_cache, variables)
        
        # Small delay between queries
        await asyncio.sleep(0.01)
    
    # Print summary
    summary = cache_monitoring.get_summary()
    logger.info(f"Simulation complete. Cache hit rate: {summary['hit_rate']:.2f}%")
    logger.info(f"Total time saved: {summary['total_saved_ms']/1000:.2f} seconds")
    
    # Print per-query stats
    logger.info("Per-query statistics:")
    for name, stats in cache_monitoring.get_query_stats().items():
        total = stats["hits"] + stats["misses"]
        hit_rate = (stats["hits"] / total * 100) if total > 0 else 0
        logger.info(f"  {name}: {hit_rate:.2f}% hit rate, {stats['total_saved_ms']/1000:.2f}s saved")

if __name__ == "__main__":
    # Reset metrics before starting
    cache_monitoring.reset_metrics()
    
    # Run the simulation
    asyncio.run(run_simulation()) 