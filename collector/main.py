"""MateObserve Collector — FastAPI application entry point."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from collector.api.routes import router
from collector.aggregation.service import run_aggregation_loop, run_retention_loop
from collector.config import settings
from collector.storage.database import engine
from collector.storage.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    # Configure structured logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    # Create tables on startup (for dev; production uses Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Start aggregation background task
    agg_task = asyncio.create_task(run_aggregation_loop())
    ret_task = asyncio.create_task(run_retention_loop())
    yield
    agg_task.cancel()
    ret_task.cancel()
    try:
        await agg_task
    except asyncio.CancelledError:
        pass
    try:
        await ret_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="MateObserve Collector",
    description="🧉 Metrics collector for MateObserve — observability in 30 seconds",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["content-type", "x-api-key"],
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple per-IP sliding-window rate limiter."""

    def __init__(self, app: FastAPI, requests_per_minute: int = 120) -> None:
        super().__init__(app)
        self.rpm = requests_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self._hits[client_ip]

        # Purge entries older than 60s
        self._hits[client_ip] = window = [t for t in window if now - t < 60]

        if len(window) >= self.rpm:
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": "60"},
            )

        window.append(now)
        return await call_next(request)


app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mateobserve-collector"}
