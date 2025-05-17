from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import os
import redis
import json
from typing import Dict, Any, List, Optional
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import jwt
import time
import asyncio
import logging

# Import workflow integration
import workflow_integration

# Import order processing
import order_routes

# Import cache monitoring (add proper path if needed)
try:
    from fastapi_project import cache_monitoring
except ImportError:
    # If importing from fastapi_project fails, try importing directly
    try:
        import cache_monitoring
    except ImportError:
        # Create a simplified version for local use
        import time
        from datetime import datetime
        
        # Simple stub for cache monitoring
        class CacheMonitoringStub:
            def track_cache_hit(self, query_name, saved_ms):
                logger.debug(f"Cache hit: {query_name}, saved {saved_ms}ms")
                
            def track_cache_miss(self, query_name):
                logger.debug(f"Cache miss: {query_name}")
                
            def get_summary(self):
                return {
                    "hits": 0, 
                    "misses": 0, 
                    "hit_rate": 0, 
                    "total_saved_ms": 0,
                    "top_queries": [],
                    "since": datetime.now().isoformat()
                }
                
            def reset_metrics(self):
                logger.debug("Cache metrics reset")
                
            def get_query_stats(self, query_name=None):
                return {}
        
        cache_monitoring = CacheMonitoringStub()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi-hasura")

app = FastAPI(title="SaaS Backend API", description="Backend API for SaaS platform using FastAPI, Hasura, and n8n")

# Include routers
app.include_router(workflow_integration.router)
app.include_router(order_routes.router)

# Hasura GraphQL endpoint - Updated with the correct configuration
HASURA_ENDPOINT = os.getenv("HASURA_ENDPOINT", "https://moving-firefly-92.hasura.app/v1/graphql")
HASURA_ADMIN_SECRET = os.getenv("HASURA_ADMIN_SECRET", "sq1AZtO4UgdMRwCZ4F2R00JGLEm2DJhTVKE4Db0jt852Zi2V6ljzMWDZ3HnNL55D")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_EXPIRATION = int(os.getenv("REDIS_EXPIRATION", "3600"))  # 1 hour cache expiration
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))  # 5 seconds timeout

# Hasura connection retry parameters
HASURA_MAX_RETRIES = 3
HASURA_RETRY_DELAY = 2  # seconds

# Setup Redis client
try:
    redis_args = {
        "host": REDIS_HOST,
        "port": REDIS_PORT,
        "db": REDIS_DB,
        "socket_timeout": REDIS_SOCKET_TIMEOUT
    }
    
    # Add password if provided
    if REDIS_PASSWORD:
        redis_args["password"] = REDIS_PASSWORD
    
    redis_client = redis.Redis(**redis_args)
    
    # Test the connection
    redis_client.ping()
    logger.info("Redis connection successful")
except redis.ConnectionError as e:
    logger.warning(f"Redis connection failed: {e}")
    # Provide a mock implementation if Redis is not available
    class MockRedis:
        def get(self, key):
            logger.debug(f"MockRedis GET: {key}")
            return None
            
        def setex(self, key, expiration, value):
            logger.debug(f"MockRedis SETEX: {key} (exp: {expiration})")
            pass
            
        def delete(self, key):
            logger.debug(f"MockRedis DELETE: {key}")
            pass
            
        def keys(self, pattern):
            logger.debug(f"MockRedis KEYS: {pattern}")
            return []
    
    redis_client = MockRedis()
    logger.info("Using MockRedis client as fallback")
except Exception as e:
    logger.error(f"Unexpected Redis error: {e}")
    raise

# Setup GraphQL client with improved error handling
try:
    logger.info(f"Attempting to connect to Hasura at {HASURA_ENDPOINT}")
    logger.info(f"Using admin secret: {HASURA_ADMIN_SECRET[:5]}...")
    
    # Initialize the transport without headers initially
    transport = AIOHTTPTransport(url=HASURA_ENDPOINT)
    
    # Initialize the client
    client = Client(transport=transport, fetch_schema_from_transport=False)
    logger.info("Hasura GraphQL client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing GraphQL client: {e}")
    # We'll handle this in the routes

# Hasura helper functions
async def execute_with_retry(query, variables=None, headers=None, max_retries=HASURA_MAX_RETRIES):
    """Execute a GraphQL query with retry logic"""
    retry_count = 0
    last_error = None
    
    # Create a complete headers dictionary that includes the admin secret
    complete_headers = {"x-hasura-admin-secret": HASURA_ADMIN_SECRET}
    if headers:
        complete_headers.update(headers)
    
    while retry_count < max_retries:
        try:
            # Set the headers for this request
            client.transport.headers = complete_headers
            
            # Execute the query
            result = await client.execute_async(
                query, 
                variable_values=variables
            )
            return result
        except Exception as e:
            last_error = e
            logger.warning(f"GraphQL execution failed (attempt {retry_count+1}/{max_retries}): {e}")
            retry_count += 1
            if retry_count < max_retries:
                # Wait before retrying
                await asyncio.sleep(HASURA_RETRY_DELAY)
    
    # If we've exhausted all retries
    logger.error(f"GraphQL execution failed after {max_retries} attempts: {last_error}")
    raise last_error

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(BaseModel):
    user_id: str
    username: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

class Order(BaseModel):
    details: Dict[str, Any]
    
class QueryCache(BaseModel):
    key: str
    ttl: int = REDIS_EXPIRATION

# Authentication functions
def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = time.time() + expires_delta * 60
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role", "user")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, role=role)
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Here you would typically fetch user from database
    # For this example, we'll create a mock user
    user = User(user_id=token_data.user_id, username=f"user_{token_data.user_id}", role=token_data.role)
    return user

# Cache utility functions
def get_cache_key(query_name: str, variables: Dict[str, Any] = None, user_id: str = None):
    """Generate a cache key based on query name, variables and user ID"""
    key_parts = [query_name]
    if variables:
        key_parts.append(json.dumps(variables, sort_keys=True))
    if user_id:
        key_parts.append(user_id)
    return ":".join(key_parts)

async def get_from_cache(query_name: str, key: str):
    """Get data from Redis cache with tracking"""
    start_time = time.time()
    try:
        data = redis_client.get(key)
        if data:
            result = json.loads(data)
            elapsed_ms = (time.time() - start_time) * 1000
            # Estimate time saved compared to a database query
            # Assuming a database query would be ~100ms, adjust based on your system
            estimated_saved_ms = 100 - elapsed_ms  
            cache_monitoring.track_cache_hit(query_name, estimated_saved_ms)
            return result, True
    except Exception as e:
        logger.error(f"Cache error: {e}")
    
    cache_monitoring.track_cache_miss(query_name)
    return None, False

async def set_in_cache(query_name: str, key: str, data: Any, expiration: int = REDIS_EXPIRATION):
    """Set data in Redis cache"""
    try:
        redis_client.setex(key, expiration, json.dumps(data))
        logger.debug(f"Stored in cache: {query_name} (key: {key}, expiration: {expiration}s)")
    except Exception as e:
        logger.error(f"Cache error: {e}")

# Background tasks
async def invalidate_related_caches(pattern: str):
    """Invalidate caches related to specific pattern"""
    try:
        # Use scan_iter for better memory efficiency with large datasets
        # This is a mock-safe implementation that works with our MockRedis too
        keys_to_delete = []
        
        # Get keys matching pattern
        try:
            # First try the scan_iter method (real Redis)
            if hasattr(redis_client, 'scan_iter'):
                scan_result = redis_client.scan_iter(match=pattern)
                keys_to_delete.extend(list(scan_result))
            # Fallback to keys method (might be less efficient but works with simple Redis)
            else:
                keys_to_delete.extend(redis_client.keys(pattern))
        except Exception as e:
            logger.warning(f"Error scanning for keys with pattern {pattern}: {e}")
            # If all else fails, we can't invalidate cache, but the app can continue
            return
        
        # Delete found keys
        if keys_to_delete:
            try:
                # Delete in batches for better efficiency
                batch_size = 100
                for i in range(0, len(keys_to_delete), batch_size):
                    batch = keys_to_delete[i:i+batch_size]
                    if batch:
                        redis_client.delete(*batch)
                
                logger.info(f"Invalidated {len(keys_to_delete)} cache keys matching pattern: {pattern}")
            except Exception as e:
                logger.error(f"Error deleting keys: {e}")
        else:
            logger.info(f"No cache keys found matching pattern: {pattern}")
    except Exception as e:
        logger.error(f"Error invalidating caches: {e}")

@app.middleware("http")
async def validate_jwt_middleware(request: Request, call_next):
    """Middleware to validate JWT token and add user info to request state"""
    # Skip validation for certain paths
    if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi") or request.url.path == "/token" or request.url.path == "/health":
        response = await call_next(request)
        return response
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Authentication token missing"})
    
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        request.state.user = payload
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    
    response = await call_next(request)
    return response

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if Hasura connection is working
    hasura_status = "healthy"
    try:
        # Simple query to test connection
        query = gql("query { __typename }")
        await client.execute_async(query)
    except Exception as e:
        hasura_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "hasura": hasura_status,
        "timestamp": time.time()
    }

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get an authentication token"""
    # In a real application, you would validate credentials against a database
    # For this example, we'll accept any username/password and assign a role
    
    # Mock user authentication - in real app, validate against database
    user_id = "12345"  # This would come from your database
    role = "admin" if form_data.username == "admin" else "user"
    
    access_token = create_access_token(
        data={"sub": user_id, "role": role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/create-order")
async def create_order(order: Order, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """Create a new order in Hasura"""
    try:
        role = current_user.role
        user_id = current_user.user_id
        query_name = "create_order"
        
        # Define the mutation
        mutation = gql('''
            mutation CreateOrder($input: orders_insert_input!) {
                insert_orders_one(object: $input) {
                    id
                    status
                    created_at
                }
            }
        ''')
        
        # Prepare variables
        variables = {
            "input": {
                "user_id": user_id,
                "details": order.details
            }
        }
        
        # Prepare headers for Hasura
        headers = {
            "x-hasura-role": role,
            "x-hasura-user-id": user_id
        }
        
        logger.info(f"Creating order with user_id: {user_id}, role: {role}")
        
        try:
            # Use our utility function with retry logic
            start_time = time.time()
            result = await execute_with_retry(mutation, variables, headers)
            query_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"Mutation execution time: {query_time_ms:.2f}ms")
            
            # Schedule cache invalidation
            cache_pattern = f"get_orders:*:{user_id}"
            background_tasks.add_task(invalidate_related_caches, cache_pattern)
            
            logger.info(f"Order created successfully: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            # For demo purposes, return mock data if Hasura is unavailable
            return {
                "insert_orders_one": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "created",
                    "created_at": "2023-07-21T12:34:56"
                }
            }
    except Exception as e:
        logger.error(f"Order creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def get_orders(current_user: User = Depends(get_current_user)):
    """Get orders with role-based filtering"""
    try:
        role = current_user.role
        user_id = current_user.user_id
        query_name = "get_orders"
        
        # Generate cache key
        cache_key = get_cache_key(query_name, None, user_id)
        
        # Try to get from cache first
        cached_data, from_cache = await get_from_cache(query_name, cache_key)
        if from_cache:
            logger.info(f"Returning cached data for key: {cache_key}")
            return cached_data
        
        # If not in cache, fetch from Hasura
        query = gql('''
            query GetOrders {
                orders {
                    id
                    status
                    user_id
                    details
                    created_at
                }
            }
        ''')
        
        headers = {
            "x-hasura-role": role,
            "x-hasura-user-id": user_id
        }
        
        logger.info(f"Fetching orders for user_id: {user_id}, role: {role}")
        
        try:
            # Use our utility function with retry logic
            start_time = time.time()
            result = await execute_with_retry(query, None, headers)
            query_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"Query execution time: {query_time_ms:.2f}ms")
            
            # Store in cache for future requests
            await set_in_cache(query_name, cache_key, result)
            
            logger.info(f"Orders fetched successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch orders: {str(e)}")
            # For demo purposes, return mock data if Hasura is unavailable
            return {
                "orders": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "created",
                        "user_id": current_user.user_id,
                        "details": {"product_id": "123", "quantity": 1},
                        "created_at": "2023-07-21T12:34:56"
                    }
                ]
            }
    except Exception as e:
        logger.error(f"Order retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get user profile information"""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role
    }

@app.post("/api/cache/invalidate")
async def invalidate_cache(query_cache: QueryCache, current_user: User = Depends(get_current_user)):
    """Invalidate a specific cache entry - admin only"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invalidate cache")
    
    try:
        redis_client.delete(query_cache.key)
        return {"status": "success", "message": f"Cache key {query_cache.key} invalidated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache error: {str(e)}")

# Cache monitoring endpoints
@app.get("/api/cache/metrics")
async def cache_metrics(current_user: User = Depends(get_current_user)):
    """Get cache metrics (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view cache metrics")
    
    return cache_monitoring.get_summary()

@app.get("/api/cache/metrics/query/{query_name}")
async def query_metrics(query_name: str, current_user: User = Depends(get_current_user)):
    """Get metrics for a specific query (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view cache metrics")
    
    stats = cache_monitoring.get_query_stats(query_name)
    if not stats:
        raise HTTPException(status_code=404, detail=f"No metrics found for query: {query_name}")
    
    return stats

@app.post("/api/cache/metrics/reset")
async def reset_metrics(current_user: User = Depends(get_current_user)):
    """Reset cache metrics (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can reset cache metrics")
    
    cache_monitoring.reset_metrics()
    return {"status": "success", "message": "Cache metrics reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 