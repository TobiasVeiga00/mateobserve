"""Tests for collector API routes."""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient


# Set API key before importing the app so Settings picks it up
os.environ.setdefault("MATEOBSERVE_API_KEY", "test-secret-key")
os.environ.setdefault("MATEOBSERVE_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from collector.main import app
from collector.config import settings


API_KEY = settings.api_key


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ── Health ─────────────────────────────────────────────────────────────────


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


# ── Authentication ─────────────────────────────────────────────────────────


def test_metrics_post_requires_api_key(client):
    resp = client.post("/metrics", json=[{"service": "test", "endpoint": "/", "method": "GET", "status_code": 200, "latency_ms": 10}])
    assert resp.status_code == 401


def test_metrics_post_rejects_wrong_key(client):
    resp = client.post(
        "/metrics",
        json=[{"service": "test", "endpoint": "/", "method": "GET", "status_code": 200, "latency_ms": 10}],
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_services_requires_api_key(client):
    resp = client.get("/services")
    assert resp.status_code == 401


def test_overview_requires_api_key(client):
    resp = client.get("/metrics/overview")
    assert resp.status_code == 401


def test_latency_requires_api_key(client):
    resp = client.get("/metrics/latency")
    assert resp.status_code == 401


def test_errors_requires_api_key(client):
    resp = client.get("/metrics/errors")
    assert resp.status_code == 401


def test_traffic_requires_api_key(client):
    resp = client.get("/metrics/traffic")
    assert resp.status_code == 401


def test_recent_errors_requires_api_key(client):
    resp = client.get("/metrics/errors/recent")
    assert resp.status_code == 401


# ── Ingestion validation ──────────────────────────────────────────────────


def test_metrics_post_rejects_oversized_batch(client):
    batch = [{"service": "test", "endpoint": "/", "method": "GET", "status_code": 200, "latency_ms": 1}] * 1001
    resp = client.post("/metrics", json=batch, headers={"X-API-Key": API_KEY})
    assert resp.status_code == 400
    assert "Batch too large" in resp.json()["detail"]


def test_metrics_post_rejects_invalid_status_code(client):
    resp = client.post(
        "/metrics",
        json=[{"service": "test", "endpoint": "/", "method": "GET", "status_code": 999, "latency_ms": 10}],
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 422  # Pydantic validation error


def test_metrics_post_rejects_negative_latency(client):
    resp = client.post(
        "/metrics",
        json=[{"service": "test", "endpoint": "/", "method": "GET", "status_code": 200, "latency_ms": -1}],
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 422


# ── Service name validation ──────────────────────────────────────────────


def test_overview_rejects_invalid_service_name(client):
    resp = client.get("/metrics/overview?service=<script>alert(1)</script>", headers={"X-API-Key": API_KEY})
    assert resp.status_code == 400
    assert "Invalid service name" in resp.json()["detail"]


def test_overview_accepts_valid_service_name(client):
    resp = client.get("/metrics/overview?service=my-app.v2", headers={"X-API-Key": API_KEY})
    # Should not be 400 (valid service name should be accepted)
    assert resp.status_code == 200


# ── SSE Stream ─────────────────────────────────────────────────────────────


def test_stream_requires_api_key(client):
    resp = client.get("/metrics/stream")
    assert resp.status_code == 401
