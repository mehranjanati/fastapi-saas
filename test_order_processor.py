import asyncio
import json
import uuid
from fastapi.testclient import TestClient
from main import app

# Create a test client
client = TestClient(app)

def test_create_order():
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
    
    # Token is required for API authentication - this is a basic example for testing
    # In a real application, you would get a proper token from the /token endpoint
    # and store it securely
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NSIsInJvbGUiOiJ1c2VyIn0.Gg6FQY7NH_e6sjXzIijwfD7-oTAZroACGQk0yMCFdLk"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Skip auth for testing
    app.dependency_overrides = {}
    
    try:
        # Create order via the API
        response = client.post(
            "/orders/",
            json=order_data
        )
        
        print(f"Create order response status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            order_id = response.json().get("order_id")
            
            if order_id:
                print(f"\nOrder created with ID: {order_id}")
                print("Checking order status...")
                
                # Wait for processing to complete
                import time
                time.sleep(3)
                
                # Check order status
                status_response = client.get(
                    f"/orders/{order_id}"
                )
                
                print(f"Status response status: {status_response.status_code}")
                print(f"Status: {json.dumps(status_response.json(), indent=2)}")
                
                # Get detailed information
                details_response = client.get(
                    f"/orders/{order_id}/details"
                )
                
                print(f"\nDetailed order information:")
                print(f"Details: {json.dumps(details_response.json(), indent=2)}")
                
                return {
                    "success": True,
                    "order_id": order_id,
                    "status": status_response.json()
                }
            else:
                print("No order ID returned from API")
        else:
            print(f"Error creating order: {response.text}")
        
        return {
            "success": False,
            "message": f"Error: Status code {response.status_code}"
        }
    except Exception as e:
        print(f"Error testing order creation: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

if __name__ == "__main__":
    # Run the test function
    test_create_order() 