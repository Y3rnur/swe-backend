"""Complaint schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.complaint.model import ComplaintStatus


class ComplaintCreate(BaseModel):
    """Complaint creation request schema."""

    order_id: int = Field(..., description="Order ID")
    sales_rep_id: int = Field(..., description="Sales representative user ID")
    manager_id: int = Field(..., description="Manager user ID")
    description: str = Field(
        ..., min_length=1, max_length=10000, description="Complaint description"
    )


class ComplaintStatusUpdate(BaseModel):
    """Complaint status update request schema."""

    status: ComplaintStatus = Field(..., description="New complaint status")
    resolution: str | None = Field(
        None, max_length=10000, description="Resolution text (required when resolving)"
    )


class ComplaintResponse(BaseModel):
    """Complaint response schema."""

    id: int
    order_id: int
    consumer_id: int
    sales_rep_id: int
    manager_id: int
    status: ComplaintStatus
    description: str
    resolution: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
