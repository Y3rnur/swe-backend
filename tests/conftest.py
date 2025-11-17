"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator, AsyncGenerator as TypingAsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.session import get_db
from app.main import app

# Create test database engine
test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Use NullPool for testing to avoid connection reuse issues
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Create a test database session with savepoint for rollback."""
    async with test_engine.connect() as conn:
        # Start a transaction
        trans = await conn.begin()
        try:
            # Create a session bound to this connection
            async with TestSessionLocal(bind=conn) as session:
                yield session
                # Rollback the transaction to undo all changes
                await session.rollback()
        finally:
            await trans.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> TypingAsyncGenerator[AsyncClient]:
    """Create a test client with database session override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
