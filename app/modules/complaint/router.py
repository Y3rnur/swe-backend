"""Complaint management routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.constants import ErrorMessages
from app.core.roles import Role
from app.db.session import get_db
from app.modules.complaint.model import Complaint, ComplaintStatus
from app.modules.complaint.schema import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatusUpdate,
)
from app.modules.order.model import Order
from app.modules.supplier.model import SupplierStaff
from app.modules.user.model import User
from app.utils.helpers import get_consumer_by_user_id
from app.utils.pagination import create_pagination_response

ComplaintRouter = APIRouter(prefix="/complaints", tags=["complaints"])


def _validate_status_transition(
    current_status: ComplaintStatus, new_status: ComplaintStatus
) -> None:
    """Validate state machine transitions for complaint status."""
    valid_transitions = {
        ComplaintStatus.OPEN: {ComplaintStatus.ESCALATED, ComplaintStatus.RESOLVED},
        ComplaintStatus.ESCALATED: {ComplaintStatus.RESOLVED},
        ComplaintStatus.RESOLVED: set[Any](),  # Resolved complaints cannot be changed
    }

    allowed = valid_transitions.get(current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {current_status.value} to {new_status.value}",
        )


async def _can_access_complaint(
    user: User, complaint: Complaint, db: AsyncSession
) -> bool:
    """Check if user can access the complaint."""
    # Consumer can access their own complaints
    consumer = await get_consumer_by_user_id(user.id, db)
    if consumer and complaint.consumer_id == consumer.id:
        return True

    # Sales rep can access complaints where they are the sales rep
    if complaint.sales_rep_id == user.id:
        return True

    # Manager can access complaints where they are the manager
    return complaint.manager_id == user.id


@ComplaintRouter.post(
    "", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED
)
async def create_complaint(
    complaint_data: ComplaintCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    """Create a complaint (consumer only)."""
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

    # Verify order exists and belongs to consumer
    result = await db.execute(select(Order).where(Order.id == complaint_data.order_id))
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

    # Verify sales rep exists
    result = await db.execute(
        select(User).where(User.id == complaint_data.sales_rep_id)
    )
    sales_rep = result.scalar_one_or_none()
    if not sales_rep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales representative not found",
        )

    # Verify manager exists
    result = await db.execute(select(User).where(User.id == complaint_data.manager_id))
    manager = result.scalar_one_or_none()
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manager not found",
        )

    # Check sales rep
    result = await db.execute(
        select(SupplierStaff).where(
            SupplierStaff.user_id == complaint_data.sales_rep_id,
            SupplierStaff.supplier_id == order.supplier_id,
        )
    )
    sales_rep_staff = result.scalar_one_or_none()
    if not sales_rep_staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sales representative is not associated with the order's supplier",
        )

    # Check manager
    result = await db.execute(
        select(SupplierStaff).where(
            SupplierStaff.user_id == complaint_data.manager_id,
            SupplierStaff.supplier_id == order.supplier_id,
            SupplierStaff.staff_role.in_(["manager", "owner"]),
        )
    )
    manager_staff = result.scalar_one_or_none()
    if not manager_staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manager is not associated with the order's supplier or does not have manager/owner role",
        )

    # Create complaint
    complaint = Complaint(
        order_id=complaint_data.order_id,
        consumer_id=consumer.id,
        sales_rep_id=complaint_data.sales_rep_id,
        manager_id=complaint_data.manager_id,
        status=ComplaintStatus.OPEN,
        description=complaint_data.description,
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)

    return ComplaintResponse.model_validate(complaint)


@ComplaintRouter.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    """Get a single complaint (consumer, sales rep, or manager only)."""
    # Get complaint
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )

    # Check access
    can_access = await _can_access_complaint(current_user, complaint, db)
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this complaint",
        )

    return ComplaintResponse.model_validate(complaint)


@ComplaintRouter.get(
    "", response_model=dict
)  # Will be PaginationResponse[ComplaintResponse]
async def get_complaints(
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status_filter: ComplaintStatus | None = Query(
        None, description="Filter by status", alias="status"
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get complaints (filtered by role: consumer sees own, sales rep sees assigned, manager sees assigned)."""
    query = select(Complaint)

    # Consumer: get their own complaints
    if current_user.role == Role.CONSUMER.value:
        consumer = await get_consumer_by_user_id(current_user.id, db)
        if not consumer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consumer profile not found",
            )
        query = query.where(Complaint.consumer_id == consumer.id)

    # Sales rep: get complaints where they are the sales rep
    elif current_user.role in (
        Role.SUPPLIER_OWNER.value,
        Role.SUPPLIER_MANAGER.value,
        Role.SUPPLIER_SALES.value,
    ):
        # Sales rep sees complaints where they are sales_rep_id
        # Manager sees complaints where they are manager_id
        # Owner/Manager can see both
        if current_user.role == Role.SUPPLIER_SALES.value:
            query = query.where(Complaint.sales_rep_id == current_user.id)
        else:
            # Owner/Manager can see complaints where they are manager or sales rep
            query = query.where(
                (Complaint.manager_id == current_user.id)
                | (Complaint.sales_rep_id == current_user.id)
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.NOT_ENOUGH_PERMISSIONS,
        )

    # Apply status filter
    if status_filter:
        query = query.where(Complaint.status == status_filter)

    # Get total count
    count_query = select(func.count(Complaint.id))
    if current_user.role == Role.CONSUMER.value:
        consumer = await get_consumer_by_user_id(current_user.id, db)
        if consumer:
            count_query = count_query.where(Complaint.consumer_id == consumer.id)
    elif current_user.role in (
        Role.SUPPLIER_OWNER.value,
        Role.SUPPLIER_MANAGER.value,
        Role.SUPPLIER_SALES.value,
    ):
        if current_user.role == Role.SUPPLIER_SALES.value:
            count_query = count_query.where(Complaint.sales_rep_id == current_user.id)
        else:
            count_query = count_query.where(
                (Complaint.manager_id == current_user.id)
                | (Complaint.sales_rep_id == current_user.id)
            )
    if status_filter:
        count_query = count_query.where(Complaint.status == status_filter)

    count_result = await db.execute(count_query)
    total = count_result.scalar_one() or 0

    # Get paginated results
    query = (
        query.order_by(Complaint.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    complaints = result.scalars().all()

    # Create response
    complaint_responses = [
        ComplaintResponse.model_validate(complaint) for complaint in complaints
    ]
    return create_pagination_response(
        complaint_responses, page, size, total
    ).model_dump()


@ComplaintRouter.patch("/{complaint_id}/status", response_model=ComplaintResponse)
async def update_complaint_status(
    complaint_id: int,
    status_update: ComplaintStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    """Update complaint status (sales rep or manager only)."""
    # Check user is sales rep or manager
    if current_user.role not in (
        Role.SUPPLIER_OWNER.value,
        Role.SUPPLIER_MANAGER.value,
        Role.SUPPLIER_SALES.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.NOT_ENOUGH_PERMISSIONS,
        )

    # Get complaint
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )

    # Check user is the sales rep or manager for this complaint
    is_sales_rep = complaint.sales_rep_id == current_user.id
    is_manager = complaint.manager_id == current_user.id

    if not (is_sales_rep or is_manager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the sales representative or manager for this complaint",
        )

    # Validate state transition
    _validate_status_transition(complaint.status, status_update.status)

    # If resolving, require resolution text
    if (
        status_update.status == ComplaintStatus.RESOLVED
        and not status_update.resolution
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolution text is required when resolving a complaint",
        )

    # Update status
    complaint.status = status_update.status
    if status_update.resolution:
        complaint.resolution = status_update.resolution
    await db.commit()
    await db.refresh(complaint)

    return ComplaintResponse.model_validate(complaint)
