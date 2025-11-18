from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.consumer.model import Consumer
    from app.modules.order.model import Order
    from app.modules.user.model import User


class ChatMessage(Base):
    """ChatMessage model."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    session: Mapped[ChatSession] = relationship(
        "ChatSession", back_populates="messages"
    )
    sender: Mapped[User] = relationship("User", back_populates="chat_messages")


class ChatSession(Base):
    """ChatSession model."""

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    consumer_id: Mapped[int] = mapped_column(
        ForeignKey("consumers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sales_rep_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    consumer: Mapped[Consumer] = relationship(
        "Consumer", back_populates="chat_sessions"
    )
    sales_rep: Mapped[User] = relationship(
        "User", foreign_keys=[sales_rep_id], back_populates="chat_sessions"
    )
    order: Mapped[Order | None] = relationship("Order", back_populates="chat_sessions")
    messages: Mapped[list[ChatMessage]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
