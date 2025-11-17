"""Chat schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    """Chat session creation request schema."""

    sales_rep_id: int = Field(..., description="Sales representative user ID")
    order_id: int | None = Field(None, description="Optional order ID to link the chat")


class ChatMessageCreate(BaseModel):
    """Chat message creation request schema."""

    text: str = Field(..., min_length=1, max_length=10000, description="Message text")
    file_url: str | None = Field(None, max_length=500, description="Optional file URL")


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""

    id: int
    session_id: int
    sender_id: int
    text: str
    file_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    """Chat session response schema."""

    id: int
    consumer_id: int
    sales_rep_id: int
    order_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
