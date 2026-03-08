"""Configuration for MateObserve SDK."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

_logger = logging.getLogger("mateobserve")


def _safe_float(value: str, env_name: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Environment variable {env_name} must be a number, got: {value!r}")


def _safe_int(value: str, env_name: str) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"Environment variable {env_name} must be an integer, got: {value!r}")


def _detect_service_name() -> str:
    """Detect service name with priority: MATEOBSERVE_SERVICE_NAME > SERVICE_NAME > main module > fallback."""
    name = os.environ.get("MATEOBSERVE_SERVICE_NAME") or os.environ.get("SERVICE_NAME")
    if name:
        return name

    main = sys.modules.get("__main__")
    if main and hasattr(main, "__file__") and main.__file__:
        return Path(main.__file__).stem

    return "python-service"


@dataclass
class MateObserveConfig:
    """SDK configuration, populated from environment variables or explicit values."""

    service_name: str = field(default_factory=_detect_service_name)
    collector_url: str = field(
        default_factory=lambda: os.environ.get(
            "MATEOBSERVE_COLLECTOR_URL", "http://localhost:8001"
        )
    )
    api_key: str = field(
        default_factory=lambda: os.environ.get("MATEOBSERVE_API_KEY", "")
    )
    flush_interval: float = field(
        default_factory=lambda: _safe_float(
            os.environ.get("MATEOBSERVE_FLUSH_INTERVAL", "2.0"),
            "MATEOBSERVE_FLUSH_INTERVAL",
        )
    )
    batch_size: int = field(
        default_factory=lambda: _safe_int(
            os.environ.get("MATEOBSERVE_BATCH_SIZE", "50"),
            "MATEOBSERVE_BATCH_SIZE",
        )
    )
    max_buffer_size: int = field(
        default_factory=lambda: _safe_int(
            os.environ.get("MATEOBSERVE_MAX_BUFFER_SIZE", "10000"),
            "MATEOBSERVE_MAX_BUFFER_SIZE",
        )
    )
    exclude_paths: list[str] = field(
        default_factory=lambda: [
            p.strip()
            for p in os.environ.get("MATEOBSERVE_EXCLUDE_PATHS", "").split(",")
            if p.strip()
        ]
    )
    enabled: bool = field(
        default_factory=lambda: os.environ.get(
            "MATEOBSERVE_ENABLED", "true"
        ).lower() in ("true", "1", "yes")
    )

    def __post_init__(self) -> None:
        parsed = urlparse(self.collector_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"collector_url must use http or https scheme, got: {parsed.scheme}")
        if not parsed.netloc:
            raise ValueError("collector_url must include a host")
        if self.flush_interval <= 0:
            raise ValueError("flush_interval must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.api_key and parsed.scheme != "https" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            _logger.warning(
                "API key is being sent over plain HTTP to %s — "
                "use HTTPS in production to protect credentials.",
                parsed.netloc,
            )
