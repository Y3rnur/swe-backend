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
    "ErrorResponse",
    "HealthCheckResponse",
    "LinkRequestCreate",
    "LinkResponse",
    "LinkStatusUpdate",
    "LoginRequest",
    "MessageResponse",
    "OrderCreate",
    "OrderItemResponse",
    "OrderResponse",
    "OrderStatusUpdate",
    "PaginationResponse",
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    "RefreshRequest",
    "SignupRequest",
    "TokenResponse",
    "UserResponse",
]
