"""Router registration."""

from fastapi import FastAPI

from app.api.routers import auth_router, main_router, users_router
from app.core.config import settings


def register_routers(app: FastAPI) -> None:
    """Register all API routers."""
    app.include_router(main_router, prefix=settings.API_V1_PREFIX)
    app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    app.include_router(users_router, prefix=settings.API_V1_PREFIX)
