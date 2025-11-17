"""Product schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str = Field(..., max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    price_kzt: Decimal = Field(..., ge=0, decimal_places=2, description="Price in KZT")
    currency: str = Field(default="KZT", max_length=3, description="Currency code")
    sku: str = Field(..., max_length=100, description="Stock keeping unit")
    stock_qty: int = Field(default=0, ge=0, description="Stock quantity")
    is_active: bool = Field(default=True, description="Whether product is active")


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = Field(None, max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    price_kzt: Decimal | None = Field(
        None, ge=0, decimal_places=2, description="Price in KZT"
    )
    currency: str | None = Field(None, max_length=3, description="Currency code")
    sku: str | None = Field(None, max_length=100, description="Stock keeping unit")
    stock_qty: int | None = Field(None, ge=0, description="Stock quantity")
    is_active: bool | None = Field(None, description="Whether product is active")


class ProductResponse(BaseModel):
    """Schema for product response."""

    id: int
    supplier_id: int
    name: str
    description: str | None
    price_kzt: Decimal
    currency: str
    sku: str
    stock_qty: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
