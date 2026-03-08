"""Tests for MateObserve middleware using a real ASGI app."""

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mateobserve.config import MateObserveConfig
from mateobserve.client import MetricsClient
from mateobserve.middleware import ObserveMiddleware


class FakeMetricsClient(MetricsClient):
    """Captures events instead of sending them."""

    def __init__(self):
        super().__init__(MateObserveConfig(collector_url="http://fake"))
        self.events: list[dict] = []

    async def start(self):
        self._started = True

    async def stop(self):
        self._started = False

    async def track(self, event: dict):
        self.events.append(event)


def _make_app(client: FakeMetricsClient, enabled: bool = True):
    async def homepage(request):
        return JSONResponse({"ok": True})

    async def error_route(request):
        raise ValueError("boom")

    config = MateObserveConfig(service_name="test-svc", enabled=enabled)
    app = Starlette(
        routes=[
            Route("/", homepage),
            Route("/error", error_route),
        ],
    )
    app.add_middleware(ObserveMiddleware, config=config, client=client)
    return app


def test_middleware_captures_successful_request():
    client = FakeMetricsClient()
    app = _make_app(client)
    tc = TestClient(app, raise_server_exceptions=False)

    resp = tc.get("/")
    assert resp.status_code == 200

    assert len(client.events) == 1
    event = client.events[0]
    assert event["service"] == "test-svc"
    assert event["endpoint"] == "/"
    assert event["method"] == "GET"
    assert event["status_code"] == 200
    assert event["latency_ms"] > 0
    assert "error" not in event


def test_middleware_captures_error():
    client = FakeMetricsClient()
    app = _make_app(client)
    tc = TestClient(app, raise_server_exceptions=False)

    resp = tc.get("/error")
    assert resp.status_code == 500

    assert len(client.events) == 1
    event = client.events[0]
    assert event["status_code"] == 500
    assert "error" in event
    assert "ValueError" in event["error"]


def test_middleware_disabled():
    client = FakeMetricsClient()
    app = _make_app(client, enabled=False)
    tc = TestClient(app, raise_server_exceptions=False)

    resp = tc.get("/")
    assert resp.status_code == 200
    assert len(client.events) == 0
