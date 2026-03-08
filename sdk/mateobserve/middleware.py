"""ASGI middleware that captures request metrics transparently."""

from __future__ import annotations

import datetime
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from mateobserve.client import MetricsClient
from mateobserve.config import MateObserveConfig


class ObserveMiddleware(BaseHTTPMiddleware):
    """Drop-in middleware for FastAPI/Starlette that captures request metrics.

    Usage::

        from mateobserve import ObserveMiddleware
        app.add_middleware(ObserveMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        config: MateObserveConfig | None = None,
        client: MetricsClient | None = None,
    ) -> None:
        super().__init__(app)
        self.config = config or MateObserveConfig()
        self.client = client or MetricsClient(self.config)
        self._started = False

    async def _ensure_started(self) -> None:
        if not self._started:
            await self.client.start()
            self._started = True

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not self.config.enabled:
            return await call_next(request)

        # Skip excluded paths (e.g. health checks)
        if self.config.exclude_paths and request.url.path in self.config.exclude_paths:
            return await call_next(request)

        await self._ensure_started()

        start = time.perf_counter()
        status_code = 500
        error: str | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            error = type(exc).__name__
            raise
        finally:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            event: dict[str, Any] = {
                "service": self.config.service_name,
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            }
            if error:
                event["error"] = error
            await self.client.track(event)
