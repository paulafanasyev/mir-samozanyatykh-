"""Pytest configuration for Мир Самозанятых"""
import pytest
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from server import Base, Settings, get_password_hash

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    """Create a fresh database session for each test."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    from server import User
    user = User(
        email="test@example.com",
        name="Test User",
        phone="+79123456789",
        hashed_password=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        level=1,
        xp=0
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
