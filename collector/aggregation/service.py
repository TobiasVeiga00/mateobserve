"""Periodic aggregation of raw metric events into time-bucketed summaries."""

from __future__ import annotations

import asyncio
import datetime
import logging
import statistics

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from collector.config import settings
from collector.storage.database import async_session
from collector.storage.models import AggregatedMetric, MetricEvent
from collector.storage import queries as _queries

logger = logging.getLogger("mateobserve.aggregation")


async def run_aggregation_loop() -> None:
    """Background task that aggregates metrics every interval."""
    logger.info("🧉 Aggregation loop started (interval=%ss)", settings.aggregation_interval_seconds)
    while True:
        try:
            await aggregate_recent()
        except Exception:
            logger.exception("Aggregation error")
        await asyncio.sleep(settings.aggregation_interval_seconds)


async def run_retention_loop() -> None:
    """Background task that cleans up old data once per hour."""
    logger.info("🧉 Retention loop started (retention=%d days)", settings.data_retention_days)
    while True:
        try:
            async with async_session() as db:
                deleted = await _queries.delete_old_events(db, settings.data_retention_days)
                if deleted:
                    logger.info("Retention cleanup: deleted %d old events", deleted)
        except Exception:
            logger.exception("Retention cleanup error")
        await asyncio.sleep(3600)  # run hourly


async def aggregate_recent() -> None:
    """Aggregate raw events from the last two intervals into per-minute buckets."""
    async with async_session() as db:
        cutoff = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
            seconds=settings.aggregation_interval_seconds * 2
        )
        result = await db.execute(
            select(MetricEvent).where(MetricEvent.timestamp >= cutoff)
        )
        events = result.scalars().all()
        if not events:
            return

        # Group by (service, endpoint, method, minute-bucket)
        buckets: dict[tuple[str, str, str, datetime.datetime], list[MetricEvent]] = {}
        for ev in events:
            ts = ev.timestamp.replace(second=0, microsecond=0)
            key = (ev.service, ev.endpoint, ev.method, ts)
            buckets.setdefault(key, []).append(ev)

        for (service, endpoint, method, bucket), group in buckets.items():
            latencies = sorted(e.latency_ms for e in group)
            error_count = sum(1 for e in group if e.status_code >= 400)

            def _percentile(data: list[float], pct: float) -> float:
                if not data:
                    return 0.0
                k = (len(data) - 1) * (pct / 100)
                f = int(k)
                c = f + 1
                if c >= len(data):
                    return data[-1]
                return data[f] + (k - f) * (data[c] - data[f])

            values = {
                "request_count": len(group),
                "error_count": error_count,
                "avg_latency_ms": round(statistics.mean(latencies), 2),
                "p50_latency_ms": round(_percentile(latencies, 50), 2),
                "p95_latency_ms": round(_percentile(latencies, 95), 2),
                "p99_latency_ms": round(_percentile(latencies, 99), 2),
                "max_latency_ms": round(max(latencies), 2),
            }

            # Atomic upsert using ON CONFLICT DO UPDATE
            stmt = pg_insert(AggregatedMetric).values(
                service=service,
                endpoint=endpoint,
                method=method,
                bucket=bucket,
                **values,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["service", "endpoint", "method", "bucket"],
                set_=values,
            )
            await db.execute(stmt)

        await db.commit()
        logger.info("Aggregated %d buckets from %d events", len(buckets), len(events))
