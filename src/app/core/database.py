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


def _normalize_database_url(url: str) -> str:
    """Build an asyncpg SQLAlchemy URL from a Render PostgreSQL URL safely."""
    value = url.strip()
    if value.startswith("postgresql+asyncpg://"):
        return value
    if value.startswith("postgresql://"):
        value = value
    elif value.startswith("postgres://"):
        value = value
    else:
        return value

    parsed = urlsplit(value)
    if not parsed.hostname:
        raise ValueError("DATABASE_URL does not contain a PostgreSQL hostname")

    username = unquote(parsed.username) if parsed.username is not None else None
    password = unquote(parsed.password) if parsed.password is not None else None
    database = parsed.path.lstrip("/") or None
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    return str(URL.create(
        drivername="postgresql+asyncpg",
        username=username,
        password=password,
        host=parsed.hostname,
        port=parsed.port,
        database=database,
        query=query,
    ))


_database_url = _normalize_database_url(settings.DATABASE_URL)

_pool_kwargs = {}
if "sqlite" not in _database_url:
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

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД (FastAPI)."""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Инициализация базы данных (создание таблиц)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def close_db():
    """Закрытие соединений с БД."""
    await engine.dispose()
    logger.info("Database connections closed")
