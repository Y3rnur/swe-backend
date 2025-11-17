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
from app.schemas.link import LinkRequestCreate, LinkResponse, LinkStatusUpdate
from app.schemas.order import (
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
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
    # Link schemas
    "LinkRequestCreate",
    "LinkResponse",
    "LinkStatusUpdate",
    # Product schemas
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    # Order schemas
    "OrderCreate",
    "OrderItemResponse",
    "OrderResponse",
    "OrderStatusUpdate",
    # User schemas
    "UserResponse",
]
