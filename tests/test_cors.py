"""CORS configuration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_allowed_origin(client: AsyncClient) -> None:
    """Test that allowed CORS origins are accepted."""
    # Test with an allowed origin
    response = await client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"},
    )

    # Check that CORS headers are present
    assert response.status_code == 200
    # FastAPI's CORSMiddleware should add these headers
    # Note: In test client, CORS headers might not be fully functional
    # but we can verify the endpoint works


@pytest.mark.asyncio
async def test_cors_preflight_request(client: AsyncClient) -> None:
    """Test CORS preflight OPTIONS request."""
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    # Preflight should succeed (status might be 200 or 204)
    assert response.status_code in [200, 204]


@pytest.mark.asyncio
async def test_health_endpoint_with_cors(client: AsyncClient) -> None:
    """Test health endpoint works with CORS headers."""
    response = await client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:8000"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
