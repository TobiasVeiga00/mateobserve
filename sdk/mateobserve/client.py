"""Async metrics client — buffers events and sends them in batches."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from mateobserve.config import MateObserveConfig

logger = logging.getLogger("mateobserve")

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 0.5  # seconds, doubled on each retry


class MetricsClient:
    """Buffers metric events and flushes them to the collector periodically."""

    def __init__(self, config: MateObserveConfig | None = None) -> None:
        self.config = config or MateObserveConfig()
        self._buffer: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task[None] | None = None
        self._http: httpx.AsyncClient | None = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        self._http = httpx.AsyncClient(timeout=10.0)
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._started = True
        logger.info(
            "🧉 MateObserve client started — service=%s collector=%s",
            self.config.service_name,
            self.config.collector_url,
        )

    async def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush()
        if self._http:
            await self._http.aclose()

    async def track(self, event: dict[str, Any]) -> None:
        async with self._lock:
            if len(self._buffer) >= self.config.max_buffer_size:
                logger.warning(
                    "MateObserve buffer full (%d events) — dropping oldest events",
                    self.config.max_buffer_size,
                )
                self._buffer = self._buffer[-(self.config.max_buffer_size // 2):]
            self._buffer.append(event)
            if len(self._buffer) >= self.config.batch_size:
                await self._flush_unlocked()

    async def _flush_loop(self) -> None:
        while self._started:
            await asyncio.sleep(self.config.flush_interval)
            await self._flush()

    async def _flush(self) -> None:
        async with self._lock:
            await self._flush_unlocked()

    async def _flush_unlocked(self) -> None:
        if not self._buffer or not self._http:
            return
        batch = self._buffer[:]
        self._buffer.clear()
        url = f"{self.config.collector_url.rstrip('/')}/metrics"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._http.post(url, json=batch, headers=headers)
                if resp.status_code < 400:
                    return  # success
                if resp.status_code < 500:
                    # Client error (e.g. 401, 400) — don't retry
                    logger.warning(
                        "MateObserve flush rejected: status=%s body=%s",
                        resp.status_code,
                        resp.text[:200],
                    )
                    return
                # Server error — retry
                logger.warning("MateObserve flush failed (attempt %d): status=%s", attempt + 1, resp.status_code)
            except Exception:
                logger.debug("MateObserve flush error (attempt %d)", attempt + 1, exc_info=True)

            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(_RETRY_BASE_DELAY * (2 ** attempt))

        logger.warning("MateObserve flush failed after %d attempts — %d events dropped", _MAX_RETRIES, len(batch))
