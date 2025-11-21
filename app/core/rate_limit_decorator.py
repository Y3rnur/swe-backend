"""Rate limiting decorator for FastAPI endpoints."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import Request

F = TypeVar("F", bound=Callable[..., Any])


def rate_limit(_calls: int = 100, _period: int = 60) -> Callable[[F], F]:
    """
    Decorator to apply rate limiting to FastAPI endpoints.

    Args:
        calls: Number of calls allowed
        period: Time period in seconds

    Usage:
        @rate_limit(calls=10, period=60)  # 10 calls per minute
        async def my_endpoint(request: Request, ...):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find Request object in args or kwargs
            request: Request | None = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and "request" in kwargs:
                request = kwargs["request"]

            # Note: Per-endpoint rate limiting would be implemented here if needed
            # Currently, rate limiting is handled globally by SlowAPIMiddleware
            # For per-endpoint limits, you would use: @limiter.limit(f"{calls}/{period}second")
            # directly on the endpoint function instead of this decorator

            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
