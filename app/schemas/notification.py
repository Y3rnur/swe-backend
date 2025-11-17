"""Notification schemas."""

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Notification response schema."""

    id: int
    recipient_id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
