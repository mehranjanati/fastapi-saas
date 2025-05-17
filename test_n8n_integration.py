"""
Test script for n8n workflow integration.
"""
import asyncio
import json
import logging
import time
import random
from datetime import datetime
import requests
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("n8n-integration-test")

# Default settings
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_WORKFLOW_ID = "test-workflow"  # Replace with your actual workflow ID

def trigger_workflow(api_url, workflow_id, data):
    """Trigger a workflow via the API"""
    url = f"{api_url}/workflow/trigger"
    
    payload = {
        "workflow_id": workflow_id,
        "data": data,
        "trigger_type": "manual"
    }
    
    headers = {
        "Content-Type": "application/json",
        # Add authorization if needed
        # "Authorization": f"Bearer {token}"
    }
    
    try:
        logger.info(f"Triggering workflow {workflow_id}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Workflow triggered successfully: {json.dumps(result)}")
            return result
        else:
            logger.error(f"Failed to trigger workflow: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error triggering workflow: {str(e)}")
        return None

def check_workflow_status(api_url, execution_id):
    """Check the status of a workflow execution"""
    url = f"{api_url}/workflow/status/{execution_id}"
    
    headers = {
        # Add authorization if needed
        # "Authorization": f"Bearer {token}"
    }
    
    try:
        logger.info(f"Checking status of execution {execution_id}...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Execution status: {json.dumps(result)}")
            return result
        else:
            logger.error(f"Failed to get execution status: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error checking execution status: {str(e)}")
        return None

def simulate_order_creation(api_url, workflow_id):
    """Simulate the creation of an order and trigger a workflow"""
    # Generate a random order
    order_id = f"ORD-{int(time.time())}-{random.randint(1000, 9999)}"
    user_id = f"user-{random.randint(1000, 9999)}"
    
    order_data = {
        "id": order_id,
        "user_id": user_id,
        "items": [
            {
                "product_id": f"PROD-{random.randint(100, 999)}",
                "name": f"Product {random.randint(1, 100)}",
                "quantity": random.randint(1, 5),
                "price": round(random.uniform(10, 200), 2)
            },
            {
                "product_id": f"PROD-{random.randint(100, 999)}",
                "name": f"Product {random.randint(1, 100)}",
                "quantity": random.randint(1, 5),
                "price": round(random.uniform(10, 200), 2)
            }
        ],
        "shipping_address": {
            "street": f"{random.randint(1, 999)} Main St",
            "city": "Example City",
            "state": "EX",
            "zip": f"{random.randint(10000, 99999)}"
        },
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    
    # Calculate total
    total = sum(item["quantity"] * item["price"] for item in order_data["items"])
    order_data["total"] = round(total, 2)
    
    # Trigger workflow
    result = trigger_workflow(api_url, workflow_id, order_data)
    
    if result and result.get("success") and result.get("execution_id"):
        # Check execution status after a delay
        execution_id = result["execution_id"]
        time.sleep(2)  # Wait for workflow to process
        status_result = check_workflow_status(api_url, execution_id)
        
        return {
            "order": order_data,
            "workflow_result": result,
            "execution_status": status_result
        }
    
    return {
        "order": order_data,
        "workflow_result": result,
        "execution_status": None
    }

def test_webhook_endpoint(api_url, event_type="test_event"):
    """Test the webhook endpoint"""
    url = f"{api_url}/workflow/webhook"
    
    payload = {
        "event_type": event_type,
        "payload": {
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "Test webhook payload",
                "value": random.randint(1, 100)
            }
        },
        "timestamp": datetime.now().isoformat()
    }
    
    headers = {
        "Content-Type": "application/json",
        # Add authorization if needed
        # "Authorization": f"Bearer {token}"
    }
    
    try:
        logger.info(f"Testing webhook endpoint with event_type: {event_type}...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Webhook processed successfully: {json.dumps(result)}")
            return result
        else:
            logger.error(f"Failed to process webhook: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error testing webhook: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Test n8n workflow integration")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help=f"FastAPI URL (default: {DEFAULT_API_URL})")
    parser.add_argument("--workflow-id", default=DEFAULT_WORKFLOW_ID, help=f"n8n workflow ID (default: {DEFAULT_WORKFLOW_ID})")
    parser.add_argument("--test-type", choices=["trigger", "webhook", "all"], default="all", help="Type of test to run")
    parser.add_argument("--count", type=int, default=1, help="Number of test iterations to run")
    
    args = parser.parse_args()
    
    logger.info(f"Starting n8n integration test with API URL: {args.api_url}")
    
    for i in range(args.count):
        iteration = f"{i+1}/{args.count}"
        logger.info(f"Test iteration {iteration}")
        
        if args.test_type in ["trigger", "all"]:
            logger.info(f"[{iteration}] Testing workflow trigger...")
            result = simulate_order_creation(args.api_url, args.workflow_id)
            logger.info(f"[{iteration}] Workflow trigger test completed")
        
        if args.test_type in ["webhook", "all"]:
            logger.info(f"[{iteration}] Testing webhook endpoint...")
            webhook_result = test_webhook_endpoint(args.api_url)
            logger.info(f"[{iteration}] Webhook test completed")
        
        if i < args.count - 1:
            time.sleep(2)  # Wait between iterations
    
    logger.info("All tests completed")

if __name__ == "__main__":
    main() 