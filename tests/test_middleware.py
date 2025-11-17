"""Middleware tests."""

import logging

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_structured_logging_middleware_logs_request_info(
    client: AsyncClient, caplog
) -> None:
    """Test that structured logging middleware logs method, path, status, latency."""
    with caplog.at_level(logging.INFO):
        response = await client.get("/api/v1/health")

    assert response.status_code == 200

    # Check that logs contain request information
    log_records = [record for record in caplog.records if "Request" in record.message]

    # Should have at least "Request started" and "Request completed" logs
    assert len(log_records) >= 2

    # Find the "Request completed" log
    completed_log = None
    for record in log_records:
        if "Request completed" in record.message:
            completed_log = record
            break

    assert completed_log is not None, "Request completed log not found"

    # Check that it has the required fields in extra
    assert hasattr(completed_log, "method")
    assert hasattr(completed_log, "path")
    assert hasattr(completed_log, "status_code")
    assert hasattr(completed_log, "latency_ms")

    # Verify values
    assert completed_log.method == "GET"
    assert "/api/v1/health" in completed_log.path
    assert completed_log.status_code == 200
    assert isinstance(completed_log.latency_ms, (int, float))
    assert completed_log.latency_ms >= 0
