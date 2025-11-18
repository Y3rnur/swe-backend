"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.session import get_db
from app.main import app

# Use test database URL if available, otherwise fall back to regular database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL or settings.DATABASE_URL


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine]:
    """
    Create a test database engine (session-scoped).

    This engine is created once per test session and reused across all tests.
    Using NullPool to avoid connection reuse issues in tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Disable SQL logging in tests unless debugging
        poolclass=NullPool,  # No connection pooling for tests
    )

    yield engine

    # Cleanup: dispose engine after all tests complete
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """
    Create a test database session with automatic rollback.

    Each test gets its own transaction that's rolled back after the test,
    ensuring test isolation and keeping the database clean.
    """
    async with test_engine.connect() as connection:
        # Start a transaction
        transaction = await connection.begin()

        # Create a session bound to this connection
        TestSessionLocal = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with TestSessionLocal() as session:
            yield session
            # Rollback to undo all changes made in this test
            await session.rollback()

        # Rollback the outer transaction
        await transaction.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """
    Create a test HTTP client with database session override.

    This fixture provides an AsyncClient that can make requests to the FastAPI app.
    The database dependency is overridden to use the test session.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        """Override the get_db dependency with the test session."""
        yield db_session

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup: remove dependency overrides after test
    app.dependency_overrides.clear()
