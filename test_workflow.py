import asyncio
import json
from workflow_integration import trigger_workflow, get_workflow_status

async def test_workflow_trigger():
    """Test triggering a workflow"""
    print("Testing workflow trigger...")
    
    # Example data to send to the workflow
    test_data = {
        "order_id": "test-123",
        "user_id": "user-456",
        "items": [
            {
                "product_id": "prod-789",
                "name": "Test Product",
                "quantity": 2,
                "price": 29.99
            }
        ],
        "total": 59.98,
        "status": "pending"
    }
    
    # Use a more descriptive workflow ID
    workflow_id = "order-process"
    
    # Trigger the workflow
    result = await trigger_workflow(workflow_id, test_data)
    
    print(f"Trigger result: {json.dumps(result, indent=2)}")
    
    # If workflow execution was successful, check status
    if result.get("success") and result.get("execution_id"):
        execution_id = result["execution_id"]
        
        print(f"\nChecking execution status for ID: {execution_id}")
        
        # Wait a moment for the workflow to process
        await asyncio.sleep(2)
        
        # Check execution status
        status = await get_workflow_status(execution_id)
        print(f"Execution status: {json.dumps(status, indent=2)}")
    
    return result

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(test_workflow_trigger()) 