"""Collector service configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://mateobserve:mateobserve@localhost:5432/mateobserve"
    redis_url: str = "redis://localhost:6379/0"
    api_key: str = ""
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:4000"]
    aggregation_interval_seconds: int = 15
    max_batch_size: int = 1000
    data_retention_days: int = 7
    rate_limit_per_minute: int = 120

    model_config = {"env_prefix": "MATEOBSERVE_"}


settings = Settings()

# Warn loudly if API key is not configured
if not settings.api_key:
    import logging as _logging
    _logging.getLogger("mateobserve.config").warning(
        "MATEOBSERVE_API_KEY is not set — all endpoints are unauthenticated! "
        "Set MATEOBSERVE_API_KEY for production use."
    )
