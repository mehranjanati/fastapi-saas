import asyncio
import json
import time
from order_processor import order_processor

async def test_order_processor():
    """Test the order processor directly"""
    print("Testing order processor directly...")
    
    # Create test order data
    order_data = {
        "order_id": "test-direct-123",
        "user_id": "test-user-456",
        "items": [
            {
                "product_id": "prod-789",
                "name": "Test Product",
                "quantity": 1,
                "price": 49.99
            }
        ],
        "total": 49.99
    }
    
    # Process the order
    result = await order_processor.process_order(order_data)
    
    print(f"Order processing result: {json.dumps(result, indent=2)}")
    
    # Check the order status
    order_id = result.get("order_id")
    if order_id:
        status = order_processor.get_order_status(order_id)
        print(f"\nOrder status: {json.dumps(status, indent=2)}")
    
    return result

if __name__ == "__main__":
    # Run the test function
    asyncio.run(test_order_processor()) 