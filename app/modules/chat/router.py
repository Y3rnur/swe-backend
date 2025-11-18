"""Chat management routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.constants import ErrorMessages
from app.core.roles import Role
from app.db.session import get_db
from app.modules.chat.model import ChatMessage, ChatSession
from app.modules.chat.schema import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from app.modules.order.model import Order
from app.modules.supplier.model import SupplierStaff
from app.modules.user.model import User
from app.utils.helpers import get_consumer_by_user_id
from app.utils.pagination import create_pagination_response

ChatRouter = APIRouter(prefix="/chats", tags=["chats"])


async def _is_session_participant(
    user: User, session: ChatSession, db: AsyncSession
) -> bool:
    """Check if user is a participant in the chat session."""
    # Check if user is the consumer
    consumer = await get_consumer_by_user_id(user.id, db)
    if consumer and session.consumer_id == consumer.id:
        return True

    return session.sales_rep_id == user.id


@ChatRouter.post(
    "/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """Create a chat session (consumer only)."""
    # Check user is consumer
    if current_user.role != Role.CONSUMER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.NOT_ENOUGH_PERMISSIONS,
        )

    # Get consumer
    consumer = await get_consumer_by_user_id(current_user.id, db)
    if not consumer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consumer profile not found",
        )

    # Verify sales rep exists and is a valid user
    result = await db.execute(select(User).where(User.id == session_data.sales_rep_id))
    sales_rep = result.scalar_one_or_none()
    if not sales_rep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales representative not found",
        )

    result = await db.execute(
        select(SupplierStaff).where(SupplierStaff.user_id == session_data.sales_rep_id)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a sales representative",
        )

    # If order_id is provided, verify it exists and belongs to the consumer
    if session_data.order_id:
        result = await db.execute(
            select(Order).where(Order.id == session_data.order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        if order.consumer_id != consumer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Order does not belong to you",
            )

    # Create chat session
    chat_session = ChatSession(
        consumer_id=consumer.id,
        sales_rep_id=session_data.sales_rep_id,
        order_id=session_data.order_id,
    )
    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)

    return ChatSessionResponse.model_validate(chat_session)


@ChatRouter.get(
    "/sessions", response_model=dict
)  # Will be PaginationResponse[ChatSessionResponse]
async def get_chat_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get chat sessions (consumer: own sessions, sales rep: sessions where they are sales rep)."""
    query = select(ChatSession)

    # Consumer: get their own sessions
    if current_user.role == Role.CONSUMER.value:
        consumer = await get_consumer_by_user_id(current_user.id, db)
        if not consumer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consumer profile not found",
            )
        query = query.where(ChatSession.consumer_id == consumer.id)

    # Sales rep: get sessions where they are the sales rep
    elif current_user.role in (
        Role.SUPPLIER_OWNER.value,
        Role.SUPPLIER_MANAGER.value,
        Role.SUPPLIER_SALES.value,
    ):
        query = query.where(ChatSession.sales_rep_id == current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.NOT_ENOUGH_PERMISSIONS,
        )

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count(ChatSession.id))
    if current_user.role == Role.CONSUMER.value:
        consumer = await get_consumer_by_user_id(current_user.id, db)
        if consumer:
            count_query = count_query.where(ChatSession.consumer_id == consumer.id)
    elif current_user.role in (
        Role.SUPPLIER_OWNER.value,
        Role.SUPPLIER_MANAGER.value,
        Role.SUPPLIER_SALES.value,
    ):
        count_query = count_query.where(ChatSession.sales_rep_id == current_user.id)

    count_result = await db.execute(count_query)
    total = count_result.scalar_one() or 0

    # Get paginated results
    query = (
        query.order_by(ChatSession.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    # Create response
    session_responses = [
        ChatSessionResponse.model_validate(session) for session in sessions
    ]
    return create_pagination_response(session_responses, page, size, total).model_dump()


@ChatRouter.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Create a chat message (only session participants)."""
    # Get chat session
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    # Check if user is a participant
    is_participant = await _is_session_participant(current_user, session, db)
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this chat session",
        )

    # Create message
    message = ChatMessage(
        session_id=session_id,
        sender_id=current_user.id,
        text=message_data.text,
        file_url=message_data.file_url,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return ChatMessageResponse.model_validate(message)


@ChatRouter.get(
    "/sessions/{session_id}/messages", response_model=dict
)  # Will be PaginationResponse[ChatMessageResponse]
async def get_chat_messages(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get chat messages (only session participants)."""
    # Get chat session
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    # Check if user is a participant
    is_participant = await _is_session_participant(current_user, session, db)
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this chat session",
        )

    # Get messages
    from sqlalchemy import func

    query = select(ChatMessage).where(ChatMessage.session_id == session_id)

    # Get total count
    count_query = select(func.count(ChatMessage.id)).where(
        ChatMessage.session_id == session_id
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar_one() or 0

    # Get paginated results
    query = (
        query.order_by(ChatMessage.created_at.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    # Create response
    message_responses = [ChatMessageResponse.model_validate(msg) for msg in messages]
    return create_pagination_response(message_responses, page, size, total).model_dump()
