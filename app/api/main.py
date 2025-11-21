"""API routes."""

import asyncio
import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.schemas.common import HealthCheckResponse, MessageResponse

MainRouter = APIRouter(prefix="", tags=["main"])
logger = logging.getLogger(__name__)


@MainRouter.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint."""
    return MessageResponse(message="Hello World")


async def check_database_health() -> str:
    """
    Check database health by executing a simple query.

    Returns:
        "ok" if database is healthy, "error" otherwise
    """
    try:
        # Use asyncio.wait_for to enforce timeout
        async with engine.connect() as conn:
            result = await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=settings.HEALTH_CHECK_TIMEOUT_SECONDS,
            )
            result.fetchone()  # fetchone() is not async, it returns immediately
            await conn.commit()
        return "ok"
    except TimeoutError:
        logger.error(
            "Database health check timeout",
            extra={
                "timeout_seconds": settings.HEALTH_CHECK_TIMEOUT_SECONDS,
            },
        )
        return "error"
    except Exception as e:
        logger.error(
            "Database health check failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,  # Include stack trace
        )
        return "error"


@MainRouter.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint with database status.

    Returns:
        HealthCheckResponse with overall status and database status
        - status: "ok" if all checks pass, "degraded" if DB is down
        - db: "ok" if database is reachable, "error" otherwise
    """
    db_status = await check_database_health()

    # Overall status is "degraded" if DB is down, "ok" otherwise
    overall_status = "ok" if db_status == "ok" else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        env=settings.ENV,
        db=db_status,
    )
