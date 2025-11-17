"""Order schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    """Schema for creating an order item."""

    product_id: int = Field(..., description="Product ID")
    qty: int = Field(..., gt=0, description="Quantity (must be positive)")


class OrderCreate(BaseModel):
    """Schema for creating an order."""

    supplier_id: int = Field(..., description="Supplier ID")
    items: list[OrderItemCreate] = Field(..., min_length=1, description="Order items")


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status."""

    status: OrderStatus = Field(..., description="New order status")


class OrderItemResponse(BaseModel):
    """Schema for order item response."""

    id: int
    order_id: int
    product_id: int
    qty: int
    unit_price_kzt: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    """Schema for order response."""

    id: int
    supplier_id: int
    consumer_id: int
    status: OrderStatus
    total_kzt: Decimal
    created_at: datetime
    items: list[OrderItemResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
