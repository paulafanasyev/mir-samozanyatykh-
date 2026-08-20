"""
Alembic environment configuration
MIR Samozanyatykh v8.4
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import app models and config
from app.core.config import settings
from app.core.database import Base, _normalize_database_url
from app.models import *  # noqa: F401, F403

# this is the Alembic Config object
config = context.config

# Keep the configured URL available for Alembic offline mode, but normalize it
# to a PostgreSQL URI that is compatible with the asyncpg driver used by the app.
_database_url = _normalize_database_url(settings.DATABASE_URL)
_database_url_string = _database_url.render_as_string(hide_password=False)
config.set_main_option("sqlalchemy.url", _database_url_string)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=_database_url_string,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an asyncpg engine and run Alembic migrations on it."""
    connectable = create_async_engine(
        _database_url,
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
