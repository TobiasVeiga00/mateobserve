"""Database query helpers for metrics — using pre-aggregated data when available."""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from collector.storage.models import AggregatedMetric, MetricEvent


def _since(minutes: int) -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(minutes=minutes)


async def insert_metric_events(db: AsyncSession, events: list[dict[str, Any]]) -> int:
    """Bulk-insert raw metric events. Returns count inserted."""
    objects = []
    for e in events:
        ts = e.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.datetime.fromisoformat(ts)
            except ValueError:
                ts = datetime.datetime.now(tz=datetime.timezone.utc)
        objects.append(
            MetricEvent(
                service=str(e.get("service", "unknown"))[:255],
                endpoint=str(e.get("endpoint", "/"))[:2048],
                method=str(e.get("method", "GET"))[:10].upper(),
                status_code=int(e.get("status_code", 0)),
                latency_ms=float(e.get("latency_ms", 0)),
                error=e.get("error"),
                timestamp=ts or datetime.datetime.now(tz=datetime.timezone.utc),
            )
        )
    db.add_all(objects)
    await db.commit()
    return len(objects)


async def list_services(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(
        select(
            MetricEvent.service,
            func.count().label("total_requests"),
            func.max(MetricEvent.timestamp).label("last_seen"),
        ).group_by(MetricEvent.service)
    )
    return [
        {"service": row.service, "total_requests": row.total_requests, "last_seen": row.last_seen.isoformat() if row.last_seen else None}
        for row in result.all()
    ]


# ── Aggregated queries (read from AggregatedMetric, fall back to raw) ────


async def get_overview(
    db: AsyncSession,
    service: str | None = None,
    minutes: int = 60,
) -> dict[str, Any]:
    """Overview from pre-aggregated metrics, with raw-event fallback."""
    since = _since(minutes)

    # Try aggregated data first
    q = select(
        func.coalesce(func.sum(AggregatedMetric.request_count), 0).label("total"),
        func.coalesce(func.sum(AggregatedMetric.error_count), 0).label("errors"),
        func.avg(AggregatedMetric.avg_latency_ms).label("avg_latency"),
        func.max(AggregatedMetric.max_latency_ms).label("max_latency"),
    ).where(AggregatedMetric.bucket >= since)
    if service:
        q = q.where(AggregatedMetric.service == service)
    result = await db.execute(q)
    row = result.one()
    total = int(row.total or 0)

    if total > 0:
        errors = int(row.errors or 0)
        return {
            "total_requests": total,
            "error_count": errors,
            "error_rate": round(errors / max(total, 1) * 100, 2),
            "avg_latency_ms": round(float(row.avg_latency or 0), 2),
            "max_latency_ms": round(float(row.max_latency or 0), 2),
            "requests_per_minute": round(total / max(minutes, 1), 2),
        }

    # Fall back to raw events
    q = select(
        func.count().label("total"),
        func.sum(case((MetricEvent.status_code >= 400, 1), else_=0)).label("errors"),
        func.avg(MetricEvent.latency_ms).label("avg_latency"),
        func.max(MetricEvent.latency_ms).label("max_latency"),
    ).where(MetricEvent.timestamp >= since)
    if service:
        q = q.where(MetricEvent.service == service)
    result = await db.execute(q)
    row = result.one()
    total = int(row.total or 0)
    errors = int(row.errors or 0)
    return {
        "total_requests": total,
        "error_count": errors,
        "error_rate": round(errors / max(total, 1) * 100, 2),
        "avg_latency_ms": round(float(row.avg_latency or 0), 2),
        "max_latency_ms": round(float(row.max_latency or 0), 2),
        "requests_per_minute": round(total / max(minutes, 1), 2),
    }


async def get_latency_stats(
    db: AsyncSession,
    service: str | None = None,
    minutes: int = 60,
) -> list[dict[str, Any]]:
    """Latency stats per endpoint from pre-aggregated metrics."""
    since = _since(minutes)

    # Try aggregated data
    q = select(
        AggregatedMetric.endpoint,
        AggregatedMetric.method,
        func.sum(AggregatedMetric.request_count).label("request_count"),
        func.avg(AggregatedMetric.avg_latency_ms).label("avg_latency_ms"),
        func.avg(AggregatedMetric.p50_latency_ms).label("p50_latency_ms"),
        func.avg(AggregatedMetric.p95_latency_ms).label("p95_latency_ms"),
        func.avg(AggregatedMetric.p99_latency_ms).label("p99_latency_ms"),
        func.max(AggregatedMetric.max_latency_ms).label("max_latency_ms"),
    ).where(AggregatedMetric.bucket >= since)
    if service:
        q = q.where(AggregatedMetric.service == service)
    q = q.group_by(AggregatedMetric.endpoint, AggregatedMetric.method)
    result = await db.execute(q)
    rows = result.all()

    if rows:
        return [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "request_count": int(r.request_count),
                "avg_latency_ms": round(float(r.avg_latency_ms or 0), 2),
                "p50_latency_ms": round(float(r.p50_latency_ms or 0), 2),
                "p95_latency_ms": round(float(r.p95_latency_ms or 0), 2),
                "p99_latency_ms": round(float(r.p99_latency_ms or 0), 2),
                "max_latency_ms": round(float(r.max_latency_ms or 0), 2),
            }
            for r in rows
        ]

    # Fall back to raw events with PostgreSQL percentile_cont
    q = select(
        MetricEvent.endpoint,
        MetricEvent.method,
        func.count().label("request_count"),
        func.avg(MetricEvent.latency_ms).label("avg_latency_ms"),
        func.percentile_cont(0.5).within_group(MetricEvent.latency_ms).label("p50_latency_ms"),
        func.percentile_cont(0.95).within_group(MetricEvent.latency_ms).label("p95_latency_ms"),
        func.percentile_cont(0.99).within_group(MetricEvent.latency_ms).label("p99_latency_ms"),
        func.max(MetricEvent.latency_ms).label("max_latency_ms"),
    ).where(MetricEvent.timestamp >= since)
    if service:
        q = q.where(MetricEvent.service == service)
    q = q.group_by(MetricEvent.endpoint, MetricEvent.method)
    result = await db.execute(q)
    return [
        {
            "endpoint": r.endpoint,
            "method": r.method,
            "request_count": int(r.request_count),
            "avg_latency_ms": round(float(r.avg_latency_ms or 0), 2),
            "p50_latency_ms": round(float(r.p50_latency_ms or 0), 2),
            "p95_latency_ms": round(float(r.p95_latency_ms or 0), 2),
            "p99_latency_ms": round(float(r.p99_latency_ms or 0), 2),
            "max_latency_ms": round(float(r.max_latency_ms or 0), 2),
        }
        for r in result.all()
    ]


async def get_error_stats(
    db: AsyncSession,
    service: str | None = None,
    minutes: int = 60,
) -> list[dict[str, Any]]:
    """Error stats per endpoint from pre-aggregated metrics."""
    since = _since(minutes)

    # Try aggregated data
    q = select(
        AggregatedMetric.endpoint,
        AggregatedMetric.method,
        func.sum(AggregatedMetric.request_count).label("total"),
        func.sum(AggregatedMetric.error_count).label("errors"),
    ).where(AggregatedMetric.bucket >= since)
    if service:
        q = q.where(AggregatedMetric.service == service)
    q = q.group_by(AggregatedMetric.endpoint, AggregatedMetric.method)
    result = await db.execute(q)
    rows = result.all()

    if rows:
        return [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "total_requests": int(r.total or 0),
                "error_count": int(r.errors or 0),
                "error_rate": round(int(r.errors or 0) / max(int(r.total or 1), 1) * 100, 2),
            }
            for r in rows
        ]

    # Fall back to raw events
    q = select(
        MetricEvent.endpoint,
        MetricEvent.method,
        func.count().label("total"),
        func.sum(case((MetricEvent.status_code >= 400, 1), else_=0)).label("errors"),
    ).where(MetricEvent.timestamp >= since)
    if service:
        q = q.where(MetricEvent.service == service)
    q = q.group_by(MetricEvent.endpoint, MetricEvent.method)
    result = await db.execute(q)
    return [
        {
            "endpoint": r.endpoint,
            "method": r.method,
            "total_requests": int(r.total or 0),
            "error_count": int(r.errors or 0),
            "error_rate": round(int(r.errors or 0) / max(int(r.total or 1), 1) * 100, 2),
        }
        for r in result.all()
    ]


async def get_traffic_stats(
    db: AsyncSession,
    service: str | None = None,
    minutes: int = 60,
) -> list[dict[str, Any]]:
    """Traffic bucketed by minute from pre-aggregated metrics."""
    since = _since(minutes)

    # Try aggregated data
    q = select(
        AggregatedMetric.bucket,
        func.sum(AggregatedMetric.request_count).label("requests"),
    ).where(AggregatedMetric.bucket >= since)
    if service:
        q = q.where(AggregatedMetric.service == service)
    q = q.group_by(AggregatedMetric.bucket).order_by(AggregatedMetric.bucket)
    result = await db.execute(q)
    rows = result.all()

    if rows:
        return [
            {"bucket": r.bucket.isoformat(), "requests": int(r.requests)}
            for r in rows
        ]

    # Fall back to raw events
    q = select(MetricEvent.timestamp).where(MetricEvent.timestamp >= since)
    if service:
        q = q.where(MetricEvent.service == service)
    result = await db.execute(q)
    rows = result.all()

    buckets: dict[str, int] = {}
    for r in rows:
        ts = r.timestamp.replace(second=0, microsecond=0)
        key = ts.isoformat()
        buckets[key] = buckets.get(key, 0) + 1

    return [
        {"bucket": k, "requests": v}
        for k, v in sorted(buckets.items())
    ]


async def get_recent_errors(
    db: AsyncSession,
    service: str | None = None,
    minutes: int = 60,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return recent individual error events with full details."""
    since = _since(minutes)
    q = (
        select(MetricEvent)
        .where(MetricEvent.timestamp >= since)
        .where(MetricEvent.status_code >= 400)
        .order_by(MetricEvent.timestamp.desc())
        .limit(limit)
    )
    if service:
        q = q.where(MetricEvent.service == service)
    result = await db.execute(q)
    events = result.scalars().all()
    return [
        {
            "service": e.service,
            "endpoint": e.endpoint,
            "method": e.method,
            "status_code": e.status_code,
            "error": e.error,
            "latency_ms": round(e.latency_ms, 2),
            "timestamp": e.timestamp.isoformat(),
        }
        for e in events
    ]


async def delete_old_events(db: AsyncSession, retention_days: int) -> int:
    """Delete metric events older than retention_days. Returns count deleted."""
    cutoff = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=retention_days)
    result = await db.execute(
        MetricEvent.__table__.delete().where(MetricEvent.timestamp < cutoff)
    )
    # Also clean up old aggregated metrics
    await db.execute(
        AggregatedMetric.__table__.delete().where(AggregatedMetric.bucket < cutoff)
    )
    await db.commit()
    return result.rowcount
