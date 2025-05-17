import logging
import json
import time
import uuid
from typing import Dict, Any, Optional
from enum import Enum

# Setup logging
logger = logging.getLogger("order-processor")

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OrderProcessor:
    """Handles order processing workflow"""
    
    def __init__(self):
        """Initialize the order processor"""
        self.orders = {}
        logger.info("Order processor initialized")
    
    async def process_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an order through the workflow"""
        # Generate an order ID if not provided
        order_id = order_data.get("order_id", f"ORD-{uuid.uuid4()}")
        
        # Store order with initial status
        self.orders[order_id] = {
            "order_id": order_id,
            "data": order_data,
            "status": OrderStatus.PENDING,
            "created_at": time.time(),
            "updated_at": time.time(),
            "history": [
                {"status": OrderStatus.PENDING, "timestamp": time.time(), "message": "Order received"}
            ]
        }
        
        logger.info(f"Order {order_id} received and added to processing queue")
        
        # Process order (simulating async processing)
        try:
            # Update status to processing
            self._update_order_status(order_id, OrderStatus.PROCESSING, "Order processing started")
            
            # Validate order items
            await self._validate_order_items(order_id, order_data)
            
            # Process payment
            await self._process_payment(order_id, order_data)
            
            # Finalize order
            await self._finalize_order(order_id, order_data)
            
            # Update status to completed
            self._update_order_status(order_id, OrderStatus.COMPLETED, "Order completed successfully")
            
            logger.info(f"Order {order_id} processed successfully")
            
            return {
                "success": True,
                "order_id": order_id,
                "status": OrderStatus.COMPLETED,
                "message": "Order processed successfully"
            }
            
        except Exception as e:
            error_msg = f"Error processing order {order_id}: {str(e)}"
            logger.error(error_msg)
            
            # Update status to failed
            self._update_order_status(order_id, OrderStatus.FAILED, error_msg)
            
            return {
                "success": False,
                "order_id": order_id,
                "status": OrderStatus.FAILED,
                "message": error_msg
            }
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of an order"""
        order = self.orders.get(order_id)
        if not order:
            return None
        
        return {
            "order_id": order_id,
            "status": order["status"],
            "created_at": order["created_at"],
            "updated_at": order["updated_at"],
            "history": order["history"]
        }
    
    def _update_order_status(self, order_id: str, status: OrderStatus, message: str = "") -> None:
        """Update the status of an order"""
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found")
        
        self.orders[order_id]["status"] = status
        self.orders[order_id]["updated_at"] = time.time()
        self.orders[order_id]["history"].append({
            "status": status,
            "timestamp": time.time(),
            "message": message
        })
        
        logger.info(f"Order {order_id} status updated to {status}: {message}")
    
    async def _validate_order_items(self, order_id: str, order_data: Dict[str, Any]) -> None:
        """Validate order items"""
        items = order_data.get("items", [])
        if not items:
            raise ValueError("Order contains no items")
        
        # Simulate validation
        time.sleep(0.5)
        
        logger.info(f"Order {order_id} items validated: {len(items)} items")
    
    async def _process_payment(self, order_id: str, order_data: Dict[str, Any]) -> None:
        """Process payment for order"""
        total = order_data.get("total", 0)
        if total <= 0:
            raise ValueError("Order total must be greater than zero")
        
        # Simulate payment processing
        time.sleep(1)
        
        logger.info(f"Order {order_id} payment processed: ${total}")
    
    async def _finalize_order(self, order_id: str, order_data: Dict[str, Any]) -> None:
        """Finalize order after payment"""
        # Simulate finalization
        time.sleep(0.5)
        
        logger.info(f"Order {order_id} finalized")

# Create singleton instance
order_processor = OrderProcessor() 