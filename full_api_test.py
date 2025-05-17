import requests
import json

# Base URL for the API
base_url = 'http://localhost:8000'

def get_token():
    """Get authentication token"""
    url = f'{base_url}/token'
    data = {
        'username': 'admin',
        'password': 'password'
    }
    response = requests.post(url, data=data)
    print(f"Token Response: {response.status_code}")
    if response.status_code == 200:
        token = response.json().get('access_token')
        print(f"Got token: {token[:10]}...")
        return token
    else:
        print(f"Error: {response.text}")
        return None

def create_order(token):
    """Create a test order"""
    url = f'{base_url}/api/create-order'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'details': {
            'product_id': '123',
            'quantity': 1
        }
    }
    print(f"Using Authorization header: {headers['Authorization']}")
    response = requests.post(url, headers=headers, json=data)
    print(f"Create Order Response: {response.status_code}")
    if response.status_code == 200:
        print(f"Order Created: {response.json()}")
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def get_orders(token):
    """Get all orders"""
    url = f'{base_url}/api/orders'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    print(f"Using Authorization header: {headers['Authorization']}")
    response = requests.get(url, headers=headers)
    print(f"Get Orders Response: {response.status_code}")
    if response.status_code == 200:
        print(f"Orders: {json.dumps(response.json(), indent=2)}")
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def run_tests():
    """Run the API tests"""
    print("\n=== Testing FastAPI Endpoints ===\n")
    
    # Get authentication token
    token = get_token()
    if not token:
        print("Failed to get token. Make sure the server is running.")
        return
    
    # Create an order
    print("\n--- Testing Create Order ---\n")
    order = create_order(token)
    
    # Get all orders
    print("\n--- Testing Get Orders ---\n")
    orders = get_orders(token)
    
    print("\n=== All tests completed ===\n")

if __name__ == '__main__':
    run_tests() 