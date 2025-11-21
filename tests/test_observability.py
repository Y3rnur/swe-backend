"""Tests for observability features (health checks, logging, correlation IDs)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_check_with_db_ok(client: AsyncClient) -> None:
    """Test health check endpoint returns ok when database is healthy."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert "env" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_check_includes_correlation_id(client: AsyncClient) -> None:
    """Test that health check response includes correlation ID header."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    assert len(response.headers["X-Correlation-ID"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_correlation_id_passed_in_request(client: AsyncClient) -> None:
    """Test that custom correlation ID from request is preserved."""
    custom_correlation_id = "test-correlation-id-123"
    response = await client.get(
        "/health",
        headers={"X-Correlation-ID": custom_correlation_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == custom_correlation_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_correlation_id_generated_if_missing(client: AsyncClient) -> None:
    """Test that correlation ID is generated if not provided in request."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    # Should be a UUID format (36 characters with hyphens)
    correlation_id = response.headers["X-Correlation-ID"]
    assert len(correlation_id) == 36
    assert correlation_id.count("-") == 4


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_logging_includes_correlation_id(
    client: AsyncClient,
) -> None:
    """Test that error responses include correlation ID."""
    # Make a request that will fail (invalid endpoint)
    response = await client.get("/nonexistent-endpoint")

    assert response.status_code == 404
    # Correlation ID should still be present
    assert "X-Correlation-ID" in response.headers


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_check_with_db_degraded(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test health check shows degraded status when database is unavailable."""
    # Mock database connection to simulate outage
    from app.api import main

    async def mock_db_check() -> str:
        """Simulate database failure."""
        raise ConnectionError("Database connection failed")

    # Patch the health check function to simulate DB outage
    monkeypatch.setattr(main, "check_database_health", mock_db_check)

    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["db"] == "error"
    assert "env" in data
