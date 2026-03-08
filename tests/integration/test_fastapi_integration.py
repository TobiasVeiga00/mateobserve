"""Integration test — FastAPI app with ObserveMiddleware."""

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from mateobserve import ObserveMiddleware
from mateobserve.config import MateObserveConfig
from mateobserve.client import MetricsClient


class FakeMetricsClient(MetricsClient):
    """Captures events in memory instead of sending them."""

    def __init__(self):
        super().__init__(MateObserveConfig(collector_url="http://fake"))
        self.events: list[dict] = []

    async def start(self):
        self._started = True

    async def stop(self):
        self._started = False

    async def track(self, event: dict):
        self.events.append(event)


@pytest.fixture
def fake_client():
    return FakeMetricsClient()


@pytest.fixture
def app(fake_client):
    config = MateObserveConfig(service_name="integration-test")
    fastapi_app = FastAPI()
    fastapi_app.add_middleware(ObserveMiddleware, config=config, client=fake_client)

    @fastapi_app.get("/")
    def root():
        return {"status": "ok"}

    @fastapi_app.get("/users/{user_id}")
    def get_user(user_id: int):
        return {"id": user_id, "name": "test"}

    @fastapi_app.post("/items")
    def create_item():
        return {"id": 1, "created": True}

    return fastapi_app


def test_fastapi_middleware_captures_get(app, fake_client):
    tc = TestClient(app, raise_server_exceptions=False)
    resp = tc.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    assert len(fake_client.events) == 1
    event = fake_client.events[0]
    assert event["service"] == "integration-test"
    assert event["endpoint"] == "/"
    assert event["method"] == "GET"
    assert event["status_code"] == 200
    assert event["latency_ms"] >= 0
    assert "timestamp" in event
    assert "error" not in event


def test_fastapi_middleware_captures_post(app, fake_client):
    tc = TestClient(app, raise_server_exceptions=False)
    resp = tc.post("/items")
    assert resp.status_code == 200

    assert len(fake_client.events) == 1
    event = fake_client.events[0]
    assert event["method"] == "POST"
    assert event["endpoint"] == "/items"


def test_fastapi_middleware_captures_path_params(app, fake_client):
    tc = TestClient(app, raise_server_exceptions=False)
    resp = tc.get("/users/42")
    assert resp.status_code == 200

    assert len(fake_client.events) == 1
    event = fake_client.events[0]
    assert event["endpoint"] == "/users/42"


def test_fastapi_middleware_multiple_requests(app, fake_client):
    tc = TestClient(app, raise_server_exceptions=False)
    tc.get("/")
    tc.get("/")
    tc.post("/items")
    assert len(fake_client.events) == 3
