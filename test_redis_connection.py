import redis
import sys

def test_redis_connection():
    """Test connection to Redis server"""
    try:
        # Create Redis client - default port is 6379
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
        
        # Test connection with ping
        ping_response = r.ping()
        print(f"Connection successful! Ping response: {ping_response}")
        
        # Test basic operations
        r.set('test_key', 'Hello from Python!')
        value = r.get('test_key')
        print(f"Retrieved test value: {value.decode('utf-8')}")
        
        # Clean up
        r.delete('test_key')
        print("Test key deleted. Test completed successfully!")
        return True
    except redis.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Redis connection...")
    success = test_redis_connection()
    sys.exit(0 if success else 1) 