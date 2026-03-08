"""SQLAlchemy ORM models for metrics storage."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MetricEvent(Base):
    """Raw metric event captured from an API."""

    __tablename__ = "metric_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    service: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(2048), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_metric_events_service_ts", "service", "timestamp"),
        Index("ix_metric_events_endpoint_ts", "endpoint", "timestamp"),
    )


class AggregatedMetric(Base):
    """Pre-aggregated metrics for fast dashboard queries."""

    __tablename__ = "aggregated_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    service: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(2048), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    bucket: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    p50_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    p95_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    p99_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    __table_args__ = (
        Index("ix_agg_service_bucket", "service", "bucket"),
        Index("ix_agg_endpoint_bucket", "endpoint", "bucket"),
        Index(
            "uq_agg_service_endpoint_method_bucket",
            "service", "endpoint", "method", "bucket",
            unique=True,
        ),
    )
