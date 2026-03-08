"""Tests for MateObserve SDK metrics client."""

import asyncio

import pytest

from mateobserve.client import MetricsClient
from mateobserve.config import MateObserveConfig


@pytest.fixture
def config():
    return MateObserveConfig(
        service_name="test",
        collector_url="http://localhost:19999",  # nonexistent
        flush_interval=100.0,  # long interval so we control flushes
        batch_size=5,
    )


@pytest.mark.asyncio
async def test_client_buffers_events(config):
    client = MetricsClient(config)
    await client.start()
    try:
        await client.track({"endpoint": "/a", "status_code": 200, "latency_ms": 10})
        await client.track({"endpoint": "/b", "status_code": 200, "latency_ms": 20})
        assert len(client._buffer) == 2
    finally:
        await client.stop()


@pytest.mark.asyncio
async def test_client_flushes_at_batch_size(config):
    """When buffer reaches batch_size, it should auto-flush."""
    client = MetricsClient(config)
    await client.start()
    try:
        for i in range(5):
            await client.track({"endpoint": f"/{i}", "status_code": 200, "latency_ms": i})
        # After batch_size events, buffer should have been flushed (and failed silently)
        assert len(client._buffer) == 0
    finally:
        await client.stop()


@pytest.mark.asyncio
async def test_client_start_stop():
    config = MateObserveConfig(collector_url="http://localhost:19999")
    client = MetricsClient(config)
    await client.start()
    assert client._started is True
    await client.stop()
    assert client._started is False
