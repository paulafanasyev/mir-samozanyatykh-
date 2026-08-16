"""Tests for security module"""
import pytest
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, verify_token, generate_csrf_token,
    hash_sha256, constant_time_compare, generate_nonce
)

class TestPasswordHashing:
    def test_password_hashing(self):
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_password_hash_different_salts(self):
        password = "SamePassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2  # bcrypt uses different salts

    def test_verify_password_timing(self):
        """Test that verification works correctly"""
        password = "MySecret123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password(password + "x", hashed) is False

class TestJWT:
    def test_create_access_token(self):
        data = {"sub": "123"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        data = {"sub": "123"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["type"] == "access"

    def test_verify_invalid_token(self):
        payload = verify_token("invalid.token.here")
        assert payload is None

    def test_verify_expired_token(self):
        import time
        from datetime import timedelta
        data = {"sub": "123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        time.sleep(1)
        payload = verify_token(token)
        assert payload is None

    def test_refresh_token(self):
        data = {"sub": "123"}
        token = create_refresh_token(data)
        payload = verify_token(token, token_type="refresh")
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_wrong_token_type(self):
        data = {"sub": "123"}
        access = create_access_token(data)
        refresh = create_refresh_token(data)
        assert verify_token(access, token_type="refresh") is None
        assert verify_token(refresh, token_type="access") is None

class TestCSRF:
    def test_csrf_token_generation(self):
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert isinstance(token1, str)
        assert len(token1) > 0
        assert token1 != token2

class TestHash:
    def test_sha256(self):
        result = hash_sha256("test")
        assert len(result) == 64
        assert result == hash_sha256("test")
        assert result != hash_sha256("different")

    def test_constant_time_compare(self):
        assert constant_time_compare("abc", "abc") is True
        assert constant_time_compare("abc", "def") is False

    def test_nonce(self):
        nonce1 = generate_nonce()
        nonce2 = generate_nonce()
        assert len(nonce1) == 32
        assert nonce1 != nonce2
