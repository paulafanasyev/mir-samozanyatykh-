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


def _normalize_database_url(url: str) -> URL | str:
    """Build a SQLAlchemy URL object from a Render PostgreSQL URL.

    Render dashboard values are sometimes pasted with surrounding quotes or
    as a complete ``DATABASE_URL=...`` assignment. Normalize those harmless
    wrappers first, then pass a structured SQLAlchemy URL to the engine so
    SQLAlchemy never has to parse the original connection string again.
    """
    value = url.strip()

    if value.startswith("DATABASE_URL="):
        value = value[len("DATABASE_URL="):].strip()

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()

    if value.startswith("postgresql+asyncpg://"):
        parsed = urlsplit(value)
    elif value.startswith("postgresql://"):
        parsed = urlsplit(value)
    elif value.startswith("postgres://"):
        parsed = urlsplit(value)
    else:
        return value

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

_pool_kwargs = {}
if "sqlite" not in str(_database_url):
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
