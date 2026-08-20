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

    Passing the URL object directly to SQLAlchemy avoids a second parse of the
    connection string and safely handles URL-encoded credentials.
    """
    value = url.strip()
    if value.startswith("postgresql+asyncpg://"):
        return URL.create(
            drivername="postgresql+asyncpg",
            username=unquote(urlsplit(value).username) if urlsplit(value).username is not None else None,
            password=unquote(urlsplit(value).password) if urlsplit(value).password is not None else None,
            host=urlsplit(value).hostname,
            port=urlsplit(value).port,
            database=urlsplit(value).path.lstrip("/") or None,
            query=dict(parse_qsl(urlsplit(value).query, keep_blank_values=True)),
        )

    if value.startswith("postgresql://"):
        value = value[len("postgresql://"):]
    elif value.startswith("postgres://"):
        value = value[len("postgres://"):]
    else:
        return value

    parsed = urlsplit("postgresql://" + value)
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

# Declarative base
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД в FastAPI"""
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
    """Инициализация базы данных (создание таблиц)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def close_db():
    """Закрытие соединений с БД"""
    await engine.dispose()
    logger.info("Database connections closed")
