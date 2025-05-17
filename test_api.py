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
        return response.json().get('access_token')
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
    response = requests.post(url, headers=headers, json=data)
    print(f"Create Order Response: {response.status_code}")
    if response.status_code == 200:
        print(f"Order Created: {response.json()}")
    else:
        print(f"Error: {response.text}")

def get_orders(token):
    """Get all orders"""
    url = f'{base_url}/api/orders'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    print(f"Get Orders Response: {response.status_code}")
    if response.status_code == 200:
        print(f"Orders: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")

def test_api():
    """Run the API tests"""
    print("Testing FastAPI endpoints...")
    
    # Get authentication token
    token = get_token()
    if not token:
        print("Failed to get token. Make sure the server is running.")
        return
    
    print(f"Got token: {token[:10]}...")
    
    # Create an order
    create_order(token)
    
    # Get all orders
    get_orders(token)

if __name__ == '__main__':
    test_api() 