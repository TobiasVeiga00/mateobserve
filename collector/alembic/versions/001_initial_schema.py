"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "metric_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("service", sa.String(255), nullable=False, index=True),
        sa.Column("endpoint", sa.String(2048), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("latency_ms", sa.Float, nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_metric_events_service_ts", "metric_events", ["service", "timestamp"])
    op.create_index("ix_metric_events_endpoint_ts", "metric_events", ["endpoint", "timestamp"])

    op.create_table(
        "aggregated_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("service", sa.String(255), nullable=False),
        sa.Column("endpoint", sa.String(2048), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("p50_latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("p95_latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("p99_latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("max_latency_ms", sa.Float, nullable=False, server_default="0"),
    )
    op.create_index("ix_agg_service_bucket", "aggregated_metrics", ["service", "bucket"])
    op.create_index("ix_agg_endpoint_bucket", "aggregated_metrics", ["endpoint", "bucket"])


def downgrade() -> None:
    op.drop_table("aggregated_metrics")
    op.drop_table("metric_events")
