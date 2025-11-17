"""Application middleware."""

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(
        self,
        request: StarletteRequest,
        call_next: Callable[[StarletteRequest], Awaitable[Response]],
    ) -> Response:
        """Log request and response with structured data."""
        start_time = time.time()

        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else None

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

        response = await call_next(request)

        latency_ms = (time.time() - start_time) * 1000

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
