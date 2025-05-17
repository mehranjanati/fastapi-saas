import requests
import json
import sys

# Set environment variables for n8n connection
n8n_base_url = "http://localhost:5678"  # Default n8n port, cannot customize with --port
n8n_api_key = ""  # Add your API key if needed

# FastAPI server URL
fastapi_base_url = "http://localhost:8000"  # Adjust if your FastAPI is on a different port

def get_auth_token():
    """Get authentication token from FastAPI"""
    try:
        auth_data = {
            "username": "admin",  # Use your actual username
            "password": "admin"   # Use your actual password
        }
        
        response = requests.post(
            f"{fastapi_base_url}/token",
            data=auth_data,
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✅ Successfully obtained auth token")
            return token
        else:
            print(f"❌ Failed to get auth token. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting auth token: {e}")
        return None

def test_n8n_connection():
    """Test if n8n is accessible"""
    try:
        # Try to access the main n8n page
        response = requests.get(n8n_base_url, timeout=5)
        if response.status_code == 200:
            print("✅ n8n is running and accessible")
            return True
        else:
            print(f"❌ n8n returned status code: {response.status_code}")
            # Still return True if we get a response, even if not 200
            return True if response.status_code != 0 else False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to n8n: {e}")
        return False

def test_fastapi_integration(token=None):
    """Test FastAPI integration with n8n"""
    try:
        # Sample data for workflow
        data = {
            "workflow_id": "order-process",
            "data": {
                "user_id": "test-user-123",
                "items": [
                    {
                        "product_id": "prod-1",
                        "name": "Test Product 1",
                        "quantity": 2,
                        "price": 29.99
                    }
                ],
                "total": 59.98,
                "status": "pending"
            },
            "trigger_type": "manual"
        }
        
        # Try to trigger a workflow through FastAPI
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        fastapi_url = f"{fastapi_base_url}/workflow/trigger"
        
        print(f"Sending request to FastAPI: {fastapi_url}")
        print(f"With data: {json.dumps(data, indent=2)}")
        
        response = requests.post(
            fastapi_url,
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"Response status code: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"Response body: {json.dumps(response.json(), indent=2)}")
            print("✅ Successfully triggered workflow through FastAPI")
            return True
        else:
            print(f"Response body: {response.text}")
            print("❌ Failed to trigger workflow through FastAPI")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error with FastAPI integration: {e}")
        return False

def test_direct_n8n_webhook():
    """Test triggering an n8n webhook directly"""
    try:
        # Sample data for workflow
        data = {
            "user_id": "test-user-123",
            "items": [
                {
                    "product_id": "prod-1",
                    "name": "Test Product 1",
                    "quantity": 2,
                    "price": 29.99
                }
            ],
            "total": 59.98,
            "status": "pending"
        }
        
        # Try to trigger a test workflow directly
        headers = {"Content-Type": "application/json"}
        if n8n_api_key:
            headers["X-N8N-API-KEY"] = n8n_api_key
            
        # Use the webhook from your n8n workflow
        # You need to create a workflow with a webhook trigger and copy its URL here
        webhook_url = f"{n8n_base_url}/webhook/process-order"
        
        print(f"Sending request directly to n8n webhook: {webhook_url}")
        print(f"With data: {json.dumps(data, indent=2)}")
        
        response = requests.post(
            webhook_url,
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Successfully triggered n8n webhook directly")
            
            # If we got an execution ID, check workflow execution status
            try:
                response_json = json.loads(response.text)
                execution_id = response_json.get("executionId")
                if execution_id:
                    print(f"Workflow execution ID: {execution_id}")
                    
                    # Wait for workflow to complete and check result
                    # This is optional and depends on your use case
                    print("You can check workflow execution status in the n8n UI")
            except json.JSONDecodeError:
                pass
                
            return True
        else:
            print("❌ Failed to trigger n8n webhook directly")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error with direct webhook: {e}")
        return False

if __name__ == "__main__":
    print("===== Testing n8n Connection =====")
    # First test n8n connection
    if not test_n8n_connection():
        print("Cannot continue testing as n8n is not accessible")
        sys.exit(1)
    
    print("\n===== Testing Direct n8n Webhook =====")
    # Test direct n8n webhook
    test_direct_n8n_webhook()
    
    print("\n===== Testing FastAPI Integration =====")
    # Get auth token for FastAPI
    auth_token = get_auth_token()
    
    # Test FastAPI integration with auth token
    if auth_token:
        test_fastapi_integration(auth_token)
    else:
        print("Skipping FastAPI integration test due to missing auth token")
        # Try without auth token for debugging purposes
        print("Attempting without auth token for debugging:")
        test_fastapi_integration() 