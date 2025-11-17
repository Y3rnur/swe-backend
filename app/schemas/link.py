"""Link schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.link import LinkStatus


class LinkRequestCreate(BaseModel):
    """Schema for creating a link request."""

    supplier_id: int = Field(..., description="ID of the supplier to request link with")


class LinkStatusUpdate(BaseModel):
    """Schema for updating link status."""

    status: LinkStatus = Field(..., description="New status for the link")


class LinkResponse(BaseModel):
    """Schema for link response."""

    id: int
    consumer_id: int
    supplier_id: int
    status: LinkStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
