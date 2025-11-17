"""Application entry point."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from app.api.routers import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
from app.schemas.common import ErrorResponse

# Setup logging
setup_logging(log_level=settings.LOG_LEVEL, env=settings.ENV)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting up application...")
    yield
    logger.info("Shutting down application...")
    try:
        await engine.dispose()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.debug("Shutdown cancelled during cleanup")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(
        self,
        request: StarletteRequest,
        call_next: Callable[[StarletteRequest], Awaitable[Response]],
    ) -> Response:
        """Log request and response with structured data."""
        start_time = time.time()

        # Get request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else None

        # Log request start
        logger.info(
            "Request started",
            extra={
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "query_params": str(request.query_params)
                if request.query_params
                else None,
            },
        )

        # Process request
        response = await call_next(request)

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            "Request completed",
            extra={
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "client_ip": client_ip,
            },
        )

        return response


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            detail="Validation error",
            code="VALIDATION_ERROR",
            meta={"errors": exc.errors()},
        ).model_dump(),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            code=f"HTTP_{exc.status_code}",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="Internal server error",
            code="INTERNAL_SERVER_ERROR",
        ).model_dump(),
    )


# Include routers with API versioning
app.include_router(router, prefix=settings.API_V1_PREFIX)
