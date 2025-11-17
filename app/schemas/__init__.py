"""Schemas package."""

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.common import (
    ErrorResponse,
    HealthCheckResponse,
    MessageResponse,
    PaginationResponse,
)
from app.schemas.user import UserResponse

__all__ = [
    # Auth schemas
    "LoginRequest",
    "RefreshRequest",
    "SignupRequest",
    "TokenResponse",
    # Common schemas
    "ErrorResponse",
    "HealthCheckResponse",
    "MessageResponse",
    "PaginationResponse",
    # User schemas
    "UserResponse",
]
