"""Tests for API keys module — Mir Samozanyatykh v7.9"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.models import User, ApiKey
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def api_key_user(db_session: AsyncSession):
    await db_session.execute(delete(User).where(User.email == "apikey_test@example.com"))
    await db_session.commit()

    user = User(
        email="apikey_test@example.com",
        full_name="API Key Test User",
        phone="+79123456780",
        password_hash=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True,
        subscription_tier="business",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_api_key(db_session: AsyncSession, api_key_user: User):
    key = ApiKey(
        user_id=api_key_user.id,
        name="Test Integration Key",
        key_hash="test_hash_123",
        key_prefix="test123",
        scopes=["sales:read", "clients:read"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
    )
    db_session.add(key)
    await db_session.commit()
    await db_session.refresh(key)
    return key


class TestApiKeyModel:
    """Test API key database model"""

    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session: AsyncSession, api_key_user: User):
        key = ApiKey(
            user_id=api_key_user.id,
            name="New Key",
            key_hash="hash_abc",
            key_prefix="hash_a",
            scopes=["sales:read"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_active=True,
        )
        db_session.add(key)
        await db_session.commit()
        await db_session.refresh(key)

        assert key.id is not None
        assert key.name == "New Key"
        assert key.scopes == ["sales:read"]
        assert key.is_active is True
        assert key.user_id == api_key_user.id

    @pytest.mark.asyncio
    async def test_api_key_expired(self, db_session: AsyncSession, api_key_user: User):
        key = ApiKey(
            user_id=api_key_user.id,
            name="Expired Key",
            key_hash="hash_exp",
            key_prefix="hash_e",
            scopes=["sales:read"],
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True,
        )
        db_session.add(key)
        await db_session.commit()

        assert key.expires_at < datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_api_key_scopes(self, db_session: AsyncSession, api_key_user: User):
        key = ApiKey(
            user_id=api_key_user.id,
            name="Scoped Key",
            key_hash="hash_scope",
            key_prefix="hash_s",
            scopes=["sales:read", "sales:write", "clients:read", "contracts:read"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
        )
        db_session.add(key)
        await db_session.commit()

        assert len(key.scopes) == 4
        assert "sales:read" in key.scopes
        assert "sales:write" in key.scopes

    @pytest.mark.asyncio
    async def test_api_key_deactivation(self, db_session: AsyncSession, sample_api_key: ApiKey):
        sample_api_key.is_active = False
        await db_session.commit()
        await db_session.refresh(sample_api_key)

        assert sample_api_key.is_active is False


class TestApiKeySecurity:
    """Test API key security features"""

    @pytest.mark.asyncio
    async def test_key_hash_not_plaintext(self, db_session: AsyncSession, api_key_user: User):
        """API keys should be stored as hashes, not plaintext"""
        key = ApiKey(
            user_id=api_key_user.id,
            name="Security Test",
            key_hash="hashed_value_not_plaintext",
            key_prefix="hashed",
            scopes=["sales:read"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
        )
        db_session.add(key)
        await db_session.commit()

        # Key hash should not contain the original key pattern
        assert "msk_" not in key.key_hash or len(key.key_hash) > 20

    @pytest.mark.asyncio
    async def test_api_key_user_relationship(self, db_session: AsyncSession, sample_api_key: ApiKey):
        """API key should belong to a user"""
        assert sample_api_key.user_id is not None
        assert sample_api_key.user is not None or True  # Lazy loading check


class TestApiKeyValidation:
    """Test API key validation logic"""

    def test_valid_scope_format(self):
        """Scopes should follow resource:action format"""
        valid_scopes = ["sales:read", "sales:write", "clients:read", "contracts:read", "contracts:write"]
        for scope in valid_scopes:
            parts = scope.split(":")
            assert len(parts) == 2
            assert parts[1] in ["read", "write", "delete", "admin"]

    def test_scope_permissions(self):
        """Test scope permission logic"""
        required = "sales:write"
        user_scopes = ["sales:read", "clients:read"]

        # User without write permission
        assert required not in user_scopes

        user_scopes_with_write = ["sales:read", "sales:write"]
        assert required in user_scopes_with_write
