"""Security utilities"""
import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time password verification"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, os.getenv("SECRET_KEY", settings.SECRET_KEY), algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, os.getenv("SECRET_KEY", settings.SECRET_KEY), algorithm=settings.ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", settings.SECRET_KEY), algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None

def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)

def hash_sha256(data: str) -> str:
    """SHA-256 hash"""
    return hashlib.sha256(data.encode()).hexdigest()

def constant_time_compare(val1: str, val2: str) -> bool:
    """Constant time string comparison"""
    return hmac.compare_digest(val1.encode(), val2.encode())

def generate_nonce() -> str:
    """Generate CSP nonce"""
    return secrets.token_hex(16)
