"""Metrics ingestion and query API routes."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from secrets import compare_digest
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from collector.config import settings
from collector.storage.database import get_db, get_session
from collector.storage import queries

logger = logging.getLogger("mateobserve.api")
router = APIRouter()

MAX_BATCH_SIZE = 1000
_SERVICE_RE = re.compile(r"^[a-zA-Z0-9._-]{1,255}$")


class MetricEventInput(BaseModel):
    service: str = Field(default="unknown", max_length=255)
    endpoint: str = Field(default="/", max_length=2048)
    method: str = Field(default="GET", max_length=10)
    status_code: int = Field(default=200, ge=100, le=599)
    latency_ms: float = Field(default=0, ge=0)
    timestamp: str | None = None
    error: str | None = Field(default=None, max_length=2000)


def _check_api_key(x_api_key: str | None = Header(None)) -> None:
    if settings.api_key:
        if not x_api_key or not compare_digest(x_api_key, settings.api_key):
            logger.warning("Failed API key authentication attempt")
            raise HTTPException(status_code=401, detail="Invalid or missing API key")


def _validate_service(service: str | None) -> str | None:
    if service is None:
        return None
    if not _SERVICE_RE.match(service):
        raise HTTPException(status_code=400, detail="Invalid service name")
    return service


# ── Ingestion ────────────────────────────────────────────────────────────────


@router.post("/metrics", status_code=202)
async def ingest_metrics(
    payload: list[MetricEventInput],
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(_check_api_key),
) -> dict[str, Any]:
    """Receive a batch of metric events from SDK clients."""
    if len(payload) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"Batch too large (max {MAX_BATCH_SIZE})")
    events = [e.model_dump() for e in payload]
    count = await queries.insert_metric_events(db, events)
    return {"accepted": count}


# ── Query endpoints ──────────────────────────────────────────────────────────


@router.get("/services")
async def list_services(
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(_check_api_key),
) -> list[dict[str, Any]]:
    return await queries.list_services(db)


@router.get("/metrics/overview")
async def overview(
    service: str | None = Query(None),
    minutes: int = Query(60, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(_check_api_key),
) -> dict[str, Any]:
    return await queries.get_overview(db, service=_validate_service(service), minutes=minutes)


@router.get("/metrics/latency")
async def latency(
    service: str | None = Query(None),
    minutes: int = Query(60, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(_check_api_key),
) -> list[dict[str, Any]]:
    return await queries.get_latency_stats(db, service=_validate_service(service), minutes=minutes)


@router.get("/metrics/errors")
async def errors(
    service: str | None = Query(None),
    minutes: int = Query(60, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(_check_api_key),
) -> list[dict[str, Any]]:
    return await queries.get_error_stats(db, service=_validate_service(service), minutes=minutes)


@router.get("/metrics/traffic")
async def traffic(
    service: str | None = Query(None),
    minutes: int = Query(60, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(_check_api_key),
) -> list[dict[str, Any]]:
    return await queries.get_traffic_stats(db, service=_validate_service(service), minutes=minutes)


@router.get("/metrics/errors/recent")
async def recent_errors(
    service: str | None = Query(None),
    minutes: int = Query(60, ge=1, le=1440),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(_check_api_key),
) -> list[dict[str, Any]]:
    return await queries.get_recent_errors(db, service=_validate_service(service), minutes=minutes, limit=limit)


# ── SSE Stream ───────────────────────────────────────────────────────────────

SSE_INTERVAL = 3  # seconds between pushes


async def _stream_metrics(request: Request, service: str | None, minutes: int):
    """Generator that yields SSE events with full dashboard data."""
    while True:
        if await request.is_disconnected():
            break
        try:
            async with get_session() as db:
                data = {
                    "services": await queries.list_services(db),
                    "overview": await queries.get_overview(db, service=service, minutes=minutes),
                    "latency": await queries.get_latency_stats(db, service=service, minutes=minutes),
                    "errors": await queries.get_error_stats(db, service=service, minutes=minutes),
                    "traffic": await queries.get_traffic_stats(db, service=service, minutes=minutes),
                    "recent_errors": await queries.get_recent_errors(db, service=service, minutes=minutes, limit=50),
                }
            yield f"data: {json.dumps(data, default=str)}\n\n"
        except Exception:
            logger.exception("SSE stream error")
            yield f"data: {json.dumps({'error': 'internal'})}\n\n"
        await asyncio.sleep(SSE_INTERVAL)


@router.get("/metrics/stream")
async def metrics_stream(
    request: Request,
    service: str | None = Query(None),
    minutes: int = Query(60, ge=1, le=1440),
    _auth: None = Depends(_check_api_key),
):
    """Server-Sent Events stream of all dashboard metrics."""
    return StreamingResponse(
        _stream_metrics(request, _validate_service(service), minutes),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
