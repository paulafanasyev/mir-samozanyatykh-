"""Pytest configuration for Mir Samozanyatykh v8.4"""
import pytest
import pytest_asyncio
import secrets
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import delete

from app.core.database import Base
from app.core.security import get_password_hash
from app.models import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session):
    # Clean up any existing test user with same email
    await db_session.execute(delete(User).where(User.email == "test@example.com"))
    await db_session.commit()

    user = User(
        email="test@example.com",
        full_name="Test User",
        phone="+79123456789",
        password_hash=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
