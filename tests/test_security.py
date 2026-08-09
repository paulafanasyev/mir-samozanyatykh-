"""Security tests for Mir Samozanyatykh v6.4"""
import pytest
from datetime import datetime, timezone, timedelta


class TestPasswordHashing:
    def test_password_hashing(self):
        from app.core.security import get_password_hash, verify_password
        password = "TestPass123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)

    def test_password_strength(self):
        from app.core.security import validate_password_strength
        is_valid, msg = validate_password_strength("StrongPass123!")
        assert is_valid
        assert msg == ""

        is_valid, msg = validate_password_strength("weak")
        assert not is_valid
        assert "8 символов" in msg

        is_valid, msg = validate_password_strength("12345678")
        assert not is_valid

        # "password" fails uppercase check first
        is_valid, msg = validate_password_strength("password")
        assert not is_valid

        # "Password123" fails special char check
        is_valid, msg = validate_password_strength("Password123")
        assert not is_valid
        assert "специальный" in msg

    def test_email_validation(self):
        from app.core.security import validate_email
        assert validate_email("test@example.com")
        assert validate_email("user+tag@domain.co.uk")
        assert not validate_email("invalid")
        assert not validate_email("@example.com")

    def test_phone_validation(self):
        from app.core.security import validate_phone
        assert validate_phone("+79123456789")
        assert not validate_phone("12345")
        assert not validate_phone("+12345678901")

    def test_inn_validation(self):
        from app.core.security import validate_inn
        assert validate_inn("123456789012") == False
        assert not validate_inn("12345")
        assert not validate_inn("abcdefghijkl")


class TestTokenCreation:
    def test_access_token(self):
        from app.core.security import create_access_token, decode_token
        token, jti = create_access_token({"sub": "1", "role": "user"})
        assert token
        assert jti
        assert len(jti) > 0

        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload

    def test_refresh_token(self):
        from app.core.security import create_refresh_token, decode_token
        token, jti = create_refresh_token({"sub": "1"})
        assert token
        assert jti

        payload = decode_token(token, expected_type="refresh")
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"

    def test_csrf_token(self):
        from app.core.security import generate_csrf_token
        token = generate_csrf_token()
        assert token
        assert len(token) > 20

    def test_csp_nonce(self):
        from app.core.security import generate_csp_nonce
        nonce = generate_csp_nonce()
        assert nonce
        assert len(nonce) > 10


class TestSignature:
    def test_simple_signature(self):
        from app.core.security import generate_simple_signature, verify_simple_signature
        data = {"amount": 5000, "client": "Test"}
        sig = generate_simple_signature(data, user_id=1)
        assert "signature" in sig
        assert sig["algorithm"] == "HMAC-SHA256"
        assert sig["type"] == "simple_electronic_signature"

        assert verify_simple_signature(data, sig)
        assert not verify_simple_signature({"amount": 9999}, sig)


class TestSanitization:
    def test_sanitize_input(self):
        from app.core.security import sanitize_input
        assert sanitize_input("<script>alert(1)</script>") == "scriptalert(1)/script"
        assert sanitize_input("  hello  ") == "hello"
        assert sanitize_input("a" * 300, max_length=10) == "a" * 10

    def test_secure_filename(self):
        from app.core.security import generate_secure_filename
        fname = generate_secure_filename("document.pdf")
        assert fname.endswith(".pdf")
        assert "/" not in fname
        assert ".." not in fname
