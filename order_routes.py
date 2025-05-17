from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import json
from order_processor import order_processor
from workflow_integration import trigger_workflow

# Setup logging
logger = logging.getLogger("order-routes")

# Create router
router = APIRouter(prefix="/orders", tags=["orders"])

class OrderItem(BaseModel):
    """Model for order items"""
    product_id: str
    name: str
    quantity: int
    price: float

class OrderRequest(BaseModel):
    """Model for order requests"""
    user_id: str
    items: List[OrderItem]
    total: Optional[float] = None
    shipping_address: Optional[Dict[str, str]] = None
    
class OrderResponse(BaseModel):
    """Response model for order operations"""
    success: bool
    message: str
    order_id: Optional[str] = None
    status: Optional[str] = None
    
@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderRequest, background_tasks: BackgroundTasks):
    """Create a new order and process it"""
    try:
        # Convert OrderRequest to dictionary
        order_data = order.dict()
        
        # Calculate total if not provided
        if not order_data.get("total"):
            total = sum(item.get("quantity", 0) * item.get("price", 0) for item in order_data.get("items", []))
            order_data["total"] = round(total, 2)
        
        # Process order in background
        background_tasks.add_task(order_processor.process_order, order_data)
        
        # Try to trigger workflow if available
        background_tasks.add_task(trigger_workflow, "order-process", order_data)
        
        # Return immediate response
        return OrderResponse(
            success=True,
            message="Order received and processing started",
            order_id=order_data.get("order_id")
        )
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get status of an order"""
    order_status = order_processor.get_order_status(order_id)
    
    if not order_status:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    return OrderResponse(
        success=True,
        message="Order status retrieved",
        order_id=order_id,
        status=order_status.get("status")
    )

@router.get("/{order_id}/details")
async def get_order_details(order_id: str):
    """Get detailed information about an order"""
    order_status = order_processor.get_order_status(order_id)
    
    if not order_status:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    return order_status 