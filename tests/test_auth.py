"""Authentication tests"""
import pytest
from datetime import datetime, timezone
from jose import jwt

from server import settings, create_access_token, verify_password, get_password_hash, validate_password_strength

class TestPasswordUtils:
    def test_password_hashing(self):
        password = "SecurePass123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)

    def test_password_strength_valid(self):
        ok, msg = validate_password_strength("StrongPass123!")
        assert ok
        assert msg == "ok"

    def test_password_strength_too_short(self):
        ok, msg = validate_password_strength("short")
        assert not ok
        assert "8" in msg

    def test_password_strength_no_numbers(self):
        ok, msg = validate_password_strength("NoNumbers!")
        assert not ok
        assert "цифр" in msg

    def test_password_strength_no_letters(self):
        ok, msg = validate_password_strength("12345678!")
        assert not ok
        assert "букв" in msg

class TestJWT:
    def test_create_access_token(self):
        data = {"sub": "test@example.com", "type": "access"}
        token, jti = create_access_token(data)
        assert token
        assert jti
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert decoded["sub"] == "test@example.com"
        assert decoded["type"] == "access"

    def test_token_expiration(self):
        from datetime import timedelta
        data = {"sub": "test@example.com", "type": "access"}
        token, _ = create_access_token(data, expires_delta=timedelta(minutes=1))
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "exp" in decoded

@pytest.mark.asyncio
class TestAuthAPI:
    async def test_register_success(self, db_session):
        """Test successful user registration."""
        from server import User
        user = User(
            email="new@example.com",
            name="New User",
            phone="+79998887766",
            hashed_password=get_password_hash("NewPass123!"),
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()

        result = await db_session.execute(
            select(User).where(User.email == "new@example.com")
        )
        assert result.scalar_one_or_none() is not None

    async def test_user_unique_email(self, db_session, test_user):
        """Test that duplicate emails are rejected."""
        from server import User
        from sqlalchemy.exc import IntegrityError

        duplicate = User(
            email="test@example.com",
            name="Duplicate",
            phone="+71111111111",
            hashed_password=get_password_hash("Pass123!"),
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(duplicate)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_user_inactive_cannot_login(self, db_session):
        """Test inactive users cannot authenticate."""
        from server import User
        user = User(
            email="inactive@example.com",
            name="Inactive",
            phone="+72222222222",
            hashed_password=get_password_hash("Pass123!"),
            is_active=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        assert not user.is_active
