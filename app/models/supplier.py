from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.link import Link
    from app.models.order import Order
    from app.models.product import Product
    from app.models.supplier_staff import SupplierStaff
    from app.models.user import User


class Supplier(Base):
    """Supplier model."""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="supplier")
    products: Mapped[list[Product]] = relationship(
        "Product", back_populates="supplier"
    )
    links: Mapped[list[Link]] = relationship("Link", back_populates="supplier")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="supplier")
    staff: Mapped[list[SupplierStaff]] = relationship(
        "SupplierStaff", back_populates="supplier"
    )
