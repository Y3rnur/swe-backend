"""Pagination utilities."""

from math import ceil
from typing import TypeVar

from app.schemas.common import PaginationResponse

T = TypeVar("T")


def calculate_pages(total: int, size: int) -> int:
    """
    Calculate total number of pages.

    Args:
        total: Total number of items
        size: Number of items per page

    Returns:
        Total number of pages
    """
    return ceil(total / size) if size > 0 else 0


def create_pagination_response(
    items: list[T],
    page: int,
    size: int,
    total: int,
) -> PaginationResponse[T]:
    """
    Create a pagination response.

    Args:
        items: List of items for the current page
        page: Current page number (1-indexed)
        size: Number of items per page
        total: Total number of items

    Returns:
        PaginationResponse with items and pagination metadata
    """
    pages = calculate_pages(total, size)
    return PaginationResponse(
        items=items,
        page=page,
        size=size,
        total=total,
        pages=pages,
    )
