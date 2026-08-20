"""
Конфигурация базы данных: async PostgreSQL + SQLAlchemy
"""

from typing import AsyncGenerator
from urllib.parse import parse_qsl, unquote, urlsplit

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from .config import settings
from .logging import logger


# Shared declarative base. Alembic imports this object to collect model metadata.
Base = declarative_base()


def _normalize_database_url(url: str) -> URL:
    """Convert a Render PostgreSQL URL into a structured SQLAlchemy URL.

    Render environment values can be copied with harmless wrappers such as
    ``DATABASE_URL=...`` or surrounding quotes. We normalize those wrappers,
    validate the URI scheme and construct a SQLAlchemy URL object so the async
    engine receives a structured connection URL.
    """
    value = str(url).strip()

    if value.startswith("DATABASE_URL="):
        value = value[len("DATABASE_URL="):].strip()

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()

    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()

    if scheme not in {"postgres", "postgresql", "postgresql+asyncpg"}:
        raise ValueError(
            f"DATABASE_URL must use a PostgreSQL URI scheme; detected '{scheme or 'none'}'"
        )

    if not parsed.hostname:
        raise ValueError("DATABASE_URL does not contain a PostgreSQL hostname")

    return URL.create(
        drivername="postgresql+asyncpg",
        username=unquote(parsed.username) if parsed.username is not None else None,
        password=unquote(parsed.password) if parsed.password is not None else None,
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path.lstrip("/") or None,
        query=dict(parse_qsl(parsed.query, keep_blank_values=True)),
    )


_database_url = _normalize_database_url(settings.DATABASE_URL)

_pool_kwargs = {
    "pool_size": settings.DATABASE_POOL_SIZE,
    "max_overflow": settings.DATABASE_MAX_OVERFLOW,
}

engine: AsyncEngine = create_async_engine(
    _database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
    **_pool_kwargs,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI database dependency with safe session cleanup."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
