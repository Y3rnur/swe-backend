from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from decimal import Decimal

    from app.models.chat_session import ChatSession
    from app.models.complaint import Complaint
    from app.models.consumer import Consumer
    from app.models.order_item import OrderItem
    from app.models.supplier import Supplier


class OrderStatus(enum.Enum):
    """Order status enum."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Order(Base):
    """Order model."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consumer_id: Mapped[int] = mapped_column(
        ForeignKey("consumers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True
    )
    total_kzt: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="orders")
    consumer: Mapped[Consumer] = relationship("Consumer", back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list[ChatSession]] = relationship(
        "ChatSession", back_populates="order"
    )
    complaints: Mapped[list[Complaint]] = relationship(
        "Complaint", back_populates="order"
    )
