"""Database session tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine, get_db


def test_engine_created():
    """Test that async engine is created."""
    assert engine is not None
    assert engine.url is not None


def test_async_session_local_created():
    """Test that AsyncSessionLocal is created."""
    assert AsyncSessionLocal is not None


def test_get_db_return_type():
    """Test that get_db has correct return type annotation."""
    import inspect

    sig = inspect.signature(get_db)
    assert sig.return_annotation != inspect.Signature.empty

    # Check it's AsyncGenerator[AsyncSession, None]
    return_annotation = sig.return_annotation
    assert "AsyncGenerator" in str(return_annotation) or "AsyncGenerator" in str(
        return_annotation.__origin__ if hasattr(return_annotation, "__origin__") else ""
    )


@pytest.mark.asyncio
async def test_get_db_provides_session():
    """Test that get_db yields an AsyncSession."""
    async for session in get_db():
        assert isinstance(session, AsyncSession)
        # Break after first yield to avoid infinite loop
        break
