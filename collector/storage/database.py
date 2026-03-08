"""SQLAlchemy async engine and session factory."""

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from collector.config import settings

_extra_kwargs: dict = {}
if settings.database_url.startswith("sqlite"):
    # In-memory SQLite needs StaticPool to share one connection across calls
    _extra_kwargs = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
else:
    _extra_kwargs = {
        "pool_size": 10,
        "max_overflow": 5,
        "pool_timeout": 10,
        "pool_recycle": 3600,
    }

engine = create_async_engine(
    settings.database_url,
    echo=False,
    **_extra_kwargs,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with async_session() as session:
        yield session


@asynccontextmanager
async def get_session():
    """Standalone async context manager for use outside FastAPI Depends."""
    async with async_session() as session:
        yield session
