"""Rate limiting utilities."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.schemas.common import ErrorResponse

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def register_rate_limit_handler(app: FastAPI) -> None:
    """Register rate limit exception handler."""
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: RateLimitExceeded
    ) -> JSONResponse:
        """Handle rate limit exceeded errors."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=ErrorResponse(
                detail="Rate limit exceeded. Please try again later.",
                code="RATE_LIMIT_EXCEEDED",
                meta={"retry_after": exc.retry_after}
                if hasattr(exc, "retry_after")
                else None,
            ).model_dump(),
        )
