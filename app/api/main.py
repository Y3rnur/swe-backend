"""API routes."""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthCheckResponse, MessageResponse

MainRouter = APIRouter(prefix="", tags=["main"])


@MainRouter.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint."""
    return MessageResponse(message="Hello World")


@MainRouter.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(status="ok", env=settings.ENV)
