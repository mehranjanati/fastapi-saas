import json
import time
import pytest

def test_create_order(client):
    """Test creating a new order"""
    print("Testing order creation...")
    
    # Create a test order
    order_data = {
        "user_id": "test-user-123",
        "items": [
            {
                "product_id": "prod-1",
                "name": "Test Product 1",
                "quantity": 2,
                "price": 29.99
            },
            {
                "product_id": "prod-2",
                "name": "Test Product 2",
                "quantity": 1,
                "price": 49.99
            }
        ],
        "shipping_address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "zip": "12345"
        }
    }
    
    # Create order via the API
    print("Sending POST request to /orders/")
    response = client.post(
        "/orders/",
        json=order_data
    )
    
    # Check response
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert response_data["message"] == "Order received and processing started"
    assert "order_id" in response_data
    
    # Get the order ID
    order_id = response_data["order_id"]
    print(f"Order ID: {order_id}")
    
    # Wait for processing to complete
    print("Waiting for order processing...")
    time.sleep(3)
    
    # Import order_processor to check internal state
    from order_processor import order_processor
    print(f"Orders in processor: {order_processor.orders}")
    
    # Check order status
    print(f"Sending GET request to /orders/{order_id}")
    status_response = client.get(
        f"/orders/{order_id}"
    )
    print(f"Status response: {status_response.status_code}")
    if status_response.status_code != 200:
        print(f"Error response body: {status_response.text}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["success"] == True
    assert status_data["order_id"] == order_id
    
    # Get detailed information
    details_response = client.get(
        f"/orders/{order_id}/details"
    )
    assert details_response.status_code == 200
    details_data = details_response.json()
    assert details_data["order_id"] == order_id
    assert "status" in details_data
    assert "history" in details_data
    
    # Return the order ID for other tests
    return order_id

def test_get_nonexistent_order(client):
    """Test getting an order that doesn't exist"""
    response = client.get(
        "/orders/nonexistent-order-id"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

# Additional pytest-specific code
def test_main():
    """Main test function to run directly if needed"""
    import sys
    import os
    from fastapi.testclient import TestClient
    
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Import from the parent directory
    from main import app, get_current_user
    
    # Create a mock user for testing
    async def mock_current_user():
        return {
            "user_id": "test-user-id",
            "username": "test-user",
            "role": "user"
        }
    
    # Override the dependency
    app.dependency_overrides[get_current_user] = mock_current_user
    
    # Create a test client
    client = TestClient(app)
    
    # Run the tests
    test_create_order(client)
    test_get_nonexistent_order(client)
    print("All tests passed!")

if __name__ == "__main__":
    test_main() 