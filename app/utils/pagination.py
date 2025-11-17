"""Pagination utilities."""

from math import ceil
from typing import TypeVar

from app.schemas.common import PaginationResponse

T = TypeVar("T")


def calculate_pages(total: int, size: int) -> int:
    """Calculate total number of pages."""
    return ceil(total / size) if size > 0 else 0


def create_pagination_response(
    items: list[T], page: int, size: int, total: int
) -> PaginationResponse[T]:
    """Create a pagination response."""
    return PaginationResponse(
        items=items,
        page=page,
        size=size,
        total=total,
        pages=calculate_pages(total, size),
    )
