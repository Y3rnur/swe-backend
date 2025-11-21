"""Exception handlers."""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ErrorResponse
from app.utils.password_policy import PasswordPolicyError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with unified error response format."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = exc.errors()
        # Format errors for better readability
        formatted_errors: list[dict[str, Any]] = []
        for error in errors:
            formatted_errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                detail="Validation error: Invalid input data",
                code="VALIDATION_ERROR",
                meta={"errors": formatted_errors},
            ).model_dump(),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle Pydantic model validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                detail="Validation error: Invalid model data",
                code="VALIDATION_ERROR",
                meta={"errors": exc.errors()},
            ).model_dump(),
        )

    @app.exception_handler(PasswordPolicyError)
    async def password_policy_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: PasswordPolicyError
    ) -> JSONResponse:
        """Handle password policy validation errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(exc),
                code="PASSWORD_POLICY_ERROR",
            ).model_dump(),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: IntegrityError
    ) -> JSONResponse:
        """Handle database integrity errors (unique constraints, foreign keys, etc.)."""
        logger.warning(f"Integrity error: {exc}", exc_info=True)

        # Try to extract meaningful error message
        error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)

        # Common integrity error patterns
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            detail = "Resource already exists (unique constraint violation)"
            code = "DUPLICATE_RESOURCE"
        elif "foreign key" in error_msg.lower():
            detail = "Referenced resource does not exist"
            code = "FOREIGN_KEY_VIOLATION"
        else:
            detail = "Database integrity constraint violation"
            code = "INTEGRITY_ERROR"

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail=detail,
                code=code,
            ).model_dump(),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Handle SQLAlchemy database errors."""
        logger.error(f"Database error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="Database error occurred",
                code="DATABASE_ERROR",
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions with standardized format."""
        # Map common status codes to error codes
        status_code_map = {
            status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
            status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
            status.HTTP_403_FORBIDDEN: "FORBIDDEN",
            status.HTTP_404_NOT_FOUND: "NOT_FOUND",
            status.HTTP_409_CONFLICT: "CONFLICT",
            status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMIT_EXCEEDED",
        }

        error_code = status_code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                code=error_code,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all other unhandled exceptions."""
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=True,
            extra={"path": _request.url.path, "method": _request.method},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="Internal server error",
                code="INTERNAL_SERVER_ERROR",
            ).model_dump(),
        )
