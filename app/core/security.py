"""
Security utilities for Mir Samozanyatykh v8.2
Security Hardened: PyJWT, bcrypt, constant-time ops
"""

import jwt
import secrets
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

from passlib.context import CryptContext
from fastapi import HTTPException, status

# ✅ PyJWT (не python-jose)
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

# ✅ Современный bcrypt с cost factor 12
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# Конфигурация JWT
SECRET_KEY = None  # Устанавливается из config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def set_secret_key(key: str):
    """Set JWT secret key from config"""
    global SECRET_KEY
    SECRET_KEY = key


def hash_password(password: str) -> str:
    """Hash password with bcrypt (cost=12)"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with constant-time comparison"""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 12:
        return False, "Пароль должен содержать минимум 12 символов"
    if not any(c.isupper() for c in password):
        return False, "Нужна хотя бы одна заглавная буква"
    if not any(c.islower() for c in password):
        return False, "Нужна хотя бы одна строчная буква"
    if not any(c.isdigit() for c in password):
        return False, "Нужна хотя бы одна цифра"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Нужен хотя бы один специальный символ"
    return True, "OK"


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(16),
        "type": "access"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> tuple[str, str]:
    """Create JWT refresh token. Returns (token, jti)"""
    jti = secrets.token_urlsafe(16)
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": jti,
        "type": "refresh"
    }
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def verify_token(token: str, expected_type: str = "access") -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # ✅ Проверить тип токена
        if payload.get("type") != expected_type:
            raise HTTPException(401, "Invalid token type")

        return payload
    except ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except InvalidTokenError:
        raise HTTPException(401, "Invalid token")


def verify_access_token(token: str) -> dict:
    """Verify access token"""
    return verify_token(token, "access")


def verify_refresh_token(token: str) -> dict:
    """Verify refresh token"""
    return verify_token(token, "refresh")


def get_user_id_from_token(token: str) -> int:
    """Extract user_id from token"""
    payload = verify_access_token(token)
    return int(payload["sub"])


def hash_token(token: str) -> str:
    """SHA-256 hash of token (for storage)"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)


def constant_time_compare(val1: str, val2: str) -> bool:
    """Constant-time string comparison (prevents timing attacks)"""
    return hmac.compare_digest(val1.encode(), val2.encode())


def mask_email(email: str) -> str:
    """Mask email for logging"""
    if "@" not in email:
        return "***"
    local, domain = email.split("@")
    if len(local) <= 2:
        masked = "***"
    else:
        masked = local[:2] + "***"
    return f"{masked}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone for logging"""
    if len(phone) <= 4:
        return "***"
    return phone[:2] + "***" + phone[-2:]
