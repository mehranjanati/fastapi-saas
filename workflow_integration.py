import logging
import json
import requests
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Header
from pydantic import BaseModel

# Setup logging
logger = logging.getLogger("fastapi-n8n")

# Create router
router = APIRouter(prefix="/workflow", tags=["workflow"])

# Configuration - should be moved to environment variables
N8N_BASE_URL = "http://localhost:5678"
N8N_API_KEY = ""  # Add your API key if needed


class WorkflowTriggerRequest(BaseModel):
    """Model for workflow trigger requests"""
    workflow_id: str
    data: Dict[str, Any]
    trigger_type: Optional[str] = "manual"


class WorkflowWebhookRequest(BaseModel):
    """Model for incoming webhook data from n8n"""
    event_type: str
    payload: Dict[str, Any]
    timestamp: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Response model for workflow operations"""
    success: bool
    message: str
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


async def trigger_workflow(workflow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger an n8n workflow with data"""
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key if provided
        if N8N_API_KEY:
            headers["X-N8N-API-KEY"] = N8N_API_KEY
        
        # Construct the webhook URL
        url = f"{N8N_BASE_URL}/webhook/{workflow_id}"
        
        # Log the request
        logger.info(f"Triggering workflow {workflow_id} with data: {json.dumps(data)}")
        
        # Send request to n8n
        response = requests.post(
            url=url,
            headers=headers,
            json=data,
            timeout=10  # 10 second timeout
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Workflow {workflow_id} executed successfully")
            return {
                "success": True,
                "message": "Workflow executed successfully",
                "execution_id": result.get("executionId"),
                "data": result.get("data")
            }
        else:
            error_msg = f"Workflow execution failed with status code: {response.status_code}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "data": None
            }
    except Exception as e:
        error_msg = f"Error triggering workflow: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "data": None
        }


async def get_workflow_status(execution_id: str) -> Dict[str, Any]:
    """Get status of a workflow execution"""
    try:
        headers = {}
        if N8N_API_KEY:
            headers["X-N8N-API-KEY"] = N8N_API_KEY
        
        url = f"{N8N_BASE_URL}/executions/{execution_id}"
        
        response = requests.get(
            url=url,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "message": "Execution status retrieved",
                "status": result.get("status"),
                "finished": result.get("finished", False),
                "data": result
            }
        else:
            error_msg = f"Failed to get workflow status with code: {response.status_code}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "status": "unknown",
                "finished": False,
                "data": None
            }
    except Exception as e:
        error_msg = f"Error getting workflow status: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "status": "error",
            "finished": False,
            "data": None
        }


# API Routes
@router.post("/trigger", response_model=WorkflowResponse)
async def trigger_workflow_endpoint(request: WorkflowTriggerRequest, background_tasks: BackgroundTasks):
    """Trigger an n8n workflow"""
    result = await trigger_workflow(request.workflow_id, request.data)
    
    return WorkflowResponse(
        success=result["success"],
        message=result["message"],
        workflow_id=request.workflow_id,
        execution_id=result.get("execution_id"),
        data=result.get("data")
    )


@router.get("/status/{execution_id}", response_model=WorkflowResponse)
async def get_workflow_status_endpoint(execution_id: str):
    """Get status of a workflow execution"""
    result = await get_workflow_status(execution_id)
    
    return WorkflowResponse(
        success=result["success"],
        message=result["message"],
        execution_id=execution_id,
        data=result.get("data")
    )


@router.post("/webhook", response_model=WorkflowResponse)
async def webhook_endpoint(webhook_data: WorkflowWebhookRequest):
    """Receive webhook data from n8n"""
    try:
        event_type = webhook_data.event_type
        payload = webhook_data.payload
        
        logger.info(f"Received webhook with event_type: {event_type}")
        
        # Process based on event type
        if event_type == "order_created":
            # Handle order created event
            logger.info(f"Processing order created event: {json.dumps(payload)}")
            # Implement your business logic here
            
        elif event_type == "payment_received":
            # Handle payment received event
            logger.info(f"Processing payment received event: {json.dumps(payload)}")
            # Implement your business logic here
            
        else:
            # Handle unknown event type
            logger.warning(f"Unknown event type: {event_type}")
        
        return WorkflowResponse(
            success=True,
            message=f"Webhook processed for event: {event_type}",
            data={"event_type": event_type}
        )
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/webhook/{workflow_tag}")
async def workflow_tag_webhook(
    workflow_tag: str, 
    payload: Dict[str, Any],
    x_n8n_signature: Optional[str] = Header(None)
):
    """Handle webhook calls from n8n with specific tags"""
    try:
        logger.info(f"Received webhook for tag: {workflow_tag}")
        
        # Validate signature if provided
        if x_n8n_signature:
            # Implement signature validation logic here
            # This would verify the request is actually from n8n
            pass
        
        # Process based on workflow tag
        if workflow_tag == "order_process":
            # Process order
            logger.info(f"Processing order workflow: {json.dumps(payload)}")
            # Implement order processing logic
            
        elif workflow_tag == "notification":
            # Handle notification
            logger.info(f"Processing notification workflow: {json.dumps(payload)}")
            # Implement notification logic
            
        else:
            # Generic processing
            logger.info(f"Processing generic workflow: {workflow_tag}")
        
        return {
            "success": True,
            "message": f"Processed webhook for {workflow_tag}",
            "data": payload
        }
    except Exception as e:
        error_msg = f"Error in webhook {workflow_tag}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg) 