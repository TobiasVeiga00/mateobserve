"""Tests for MateObserve SDK configuration."""

import pytest

from mateobserve.config import MateObserveConfig, _detect_service_name


def test_default_config(monkeypatch):
    monkeypatch.delenv("MATEOBSERVE_API_KEY", raising=False)
    config = MateObserveConfig()
    # service_name is auto-detected (not a fixed value)
    assert isinstance(config.service_name, str)
    assert len(config.service_name) > 0
    assert config.collector_url == "http://localhost:8001"
    assert config.api_key == ""
    assert config.flush_interval == 2.0
    assert config.batch_size == 50
    assert config.enabled is True


def test_service_name_detection_priority(monkeypatch):
    """MATEOBSERVE_SERVICE_NAME > SERVICE_NAME > main module > fallback."""
    monkeypatch.delenv("MATEOBSERVE_SERVICE_NAME", raising=False)
    monkeypatch.delenv("SERVICE_NAME", raising=False)

    # With MATEOBSERVE_SERVICE_NAME set
    monkeypatch.setenv("MATEOBSERVE_SERVICE_NAME", "from-mate-env")
    assert _detect_service_name() == "from-mate-env"

    # With only SERVICE_NAME set
    monkeypatch.delenv("MATEOBSERVE_SERVICE_NAME")
    monkeypatch.setenv("SERVICE_NAME", "from-generic-env")
    assert _detect_service_name() == "from-generic-env"

    # With neither set — falls back to main module name
    monkeypatch.delenv("SERVICE_NAME")
    name = _detect_service_name()
    assert isinstance(name, str)
    assert len(name) > 0


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("MATEOBSERVE_SERVICE_NAME", "test-api")
    monkeypatch.setenv("MATEOBSERVE_COLLECTOR_URL", "http://collector:9000")
    monkeypatch.setenv("MATEOBSERVE_API_KEY", "secret-key")
    monkeypatch.setenv("MATEOBSERVE_FLUSH_INTERVAL", "10.0")
    monkeypatch.setenv("MATEOBSERVE_BATCH_SIZE", "50")
    monkeypatch.setenv("MATEOBSERVE_ENABLED", "false")

    config = MateObserveConfig()
    assert config.service_name == "test-api"
    assert config.collector_url == "http://collector:9000"
    assert config.api_key == "secret-key"
    assert config.flush_interval == 10.0
    assert config.batch_size == 50
    assert config.enabled is False


def test_config_explicit_values():
    config = MateObserveConfig(
        service_name="my-api",
        collector_url="http://1.2.3.4:8001",
        api_key="abc123",
    )
    assert config.service_name == "my-api"
    assert config.collector_url == "http://1.2.3.4:8001"
    assert config.api_key == "abc123"


def test_config_rejects_invalid_url():
    with pytest.raises(ValueError, match="http or https"):
        MateObserveConfig(collector_url="ftp://bad.example.com")


def test_config_rejects_negative_flush_interval():
    with pytest.raises(ValueError, match="flush_interval"):
        MateObserveConfig(flush_interval=-1.0)


def test_config_rejects_zero_batch_size():
    with pytest.raises(ValueError, match="batch_size"):
        MateObserveConfig(batch_size=0)
