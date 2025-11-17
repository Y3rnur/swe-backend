"""API dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


async def get_current_db(
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """
    Get current database session.

    Args:
        db: Database session

    Returns:
        Database session
    """
    return db
