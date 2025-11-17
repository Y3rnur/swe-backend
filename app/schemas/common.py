"""Common Pydantic schemas."""

from typing import Any

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str
    env: str


class MessageResponse(BaseModel):
    """Message response schema."""

    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    code: str
    meta: dict[str, Any] | None = None


class PaginationResponse[T](BaseModel):
    """Pagination response schema."""

    items: list[T]
    page: int
    size: int
    total: int
    pages: int
