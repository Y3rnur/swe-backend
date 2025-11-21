"""Product schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    """Schema for creating a product."""

    model_config = ConfigDict(
        strict=True,
        json_schema_extra={
            "example": {
                "name": "Premium Widget",
                "description": "High-quality widget for industrial use",
                "price_kzt": "15000.00",
                "currency": "KZT",
                "sku": "WID-001",
                "stock_qty": 100,
                "is_active": True,
            }
        },
    )

    name: str = Field(..., max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    price_kzt: Decimal = Field(..., ge=0, decimal_places=2, description="Price in KZT")
    currency: str = Field(
        default="KZT", max_length=3, description="Currency code (ISO 4217)"
    )
    sku: str = Field(
        ..., max_length=100, description="Stock keeping unit (unique per supplier)"
    )
    stock_qty: int = Field(default=0, ge=0, description="Stock quantity")
    is_active: bool = Field(default=True, description="Whether product is active")


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    model_config = ConfigDict(
        strict=True,
        json_schema_extra={
            "example": {
                "name": "Updated Premium Widget",
                "price_kzt": "16000.00",
                "stock_qty": 150,
            }
        },
    )

    name: str | None = Field(None, max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    price_kzt: Decimal | None = Field(
        None, ge=0, decimal_places=2, description="Price in KZT"
    )
    currency: str | None = Field(
        None, max_length=3, description="Currency code (ISO 4217)"
    )
    sku: str | None = Field(
        None, max_length=100, description="Stock keeping unit (unique per supplier)"
    )
    stock_qty: int | None = Field(None, ge=0, description="Stock quantity")
    is_active: bool | None = Field(None, description="Whether product is active")


class ProductResponse(BaseModel):
    """Schema for product response."""

    model_config = ConfigDict(
        from_attributes=True,
        strict=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "supplier_id": 1,
                "name": "Premium Widget",
                "description": "High-quality widget for industrial use",
                "price_kzt": "15000.00",
                "currency": "KZT",
                "sku": "WID-001",
                "stock_qty": 100,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
            }
        },
    )

    id: int = Field(..., description="Product ID")
    supplier_id: int = Field(..., description="Supplier ID")
    name: str = Field(..., description="Product name")
    description: str | None = Field(None, description="Product description")
    price_kzt: Decimal = Field(..., description="Price in KZT")
    currency: str = Field(..., description="Currency code")
    sku: str = Field(..., description="Stock keeping unit")
    stock_qty: int = Field(..., description="Stock quantity")
    is_active: bool = Field(..., description="Whether product is active")
    created_at: datetime = Field(..., description="Creation timestamp")
