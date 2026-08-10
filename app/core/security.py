"""
Безопасность: JWT, хеширование, CSRF, rate limiting
АНО ЦПС ИНН 9724016805
"""

import secrets
import hmac
import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings
from .logging import logger


# Константы
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Регулярные выражения для валидации
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^\+7\d{10}$")
INN_REGEX = re.compile(r"^\d{12}$")


def verify_password(plain: str, hashed: str) -> bool:
    """Проверка пароля с защитой от timing attacks"""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        # Constant-time dummy comparison to prevent timing attacks
        dummy_hash = pwd_context.hash("dummy")
        pwd_context.verify("dummy", dummy_hash)
        return False


def get_password_hash(password: str) -> str:
    """Хеширование пароля bcrypt"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Валидация сложности пароля по OWASP рекомендациям
    """
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    if len(password) > 128:
        return False, "Пароль слишком длинный (максимум 128)"
    if not any(c.isupper() for c in password):
        return False, "Пароль должен содержать заглавную букву"
    if not any(c.islower() for c in password):
        return False, "Пароль должен содержать строчную букву"
    if not any(c.isdigit() for c in password):
        return False, "Пароль должен содержать цифру"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Пароль должен содержать специальный символ"
    # Проверка на распространённые пароли
    common_passwords = {"password", "123456", "qwerty", "admin", "letmein"}
    if password.lower() in common_passwords:
        return False, "Слишком простой пароль"
    return True, ""


def validate_email(email: str) -> bool:
    """Валидация email"""
    if not email or len(email) > 255:
        return False
    return bool(EMAIL_REGEX.match(email))


def validate_phone(phone: str) -> bool:
    """Валидация российского телефона"""
    return bool(PHONE_REGEX.match(phone))


def validate_inn(inn: str) -> bool:
    """Валидация ИНН физического лица (12 цифр)"""
    if not inn or len(inn) != 12:
        return False
    if not inn.isdigit():
        return False
    # Контрольная сумма
    def _check_inn(inn_str: str) -> bool:
        weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        
        check1 = sum(int(inn_str[i]) * weights1[i] for i in range(10)) % 11 % 10
        if check1 != int(inn_str[10]):
            return False
        check2 = sum(int(inn_str[i]) * weights2[i] for i in range(11)) % 11 % 10
        return check2 == int(inn_str[11])
    
    return _check_inn(inn)


def generate_csrf_token() -> str:
    """Генерация CSRF токена"""
    return secrets.token_urlsafe(32)


def generate_csp_nonce() -> str:
    """Генерация nonce для CSP"""
    return secrets.token_urlsafe(16)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> Tuple[str, str]:
    """
    Создание access token с jti (JWT ID) для отзыва
    
    Returns:
        tuple: (token_string, jti)
    """
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "nbf": datetime.now(timezone.utc),
    })
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def create_refresh_token(data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Создание refresh token с jti
    
    Returns:
        tuple: (token_string, jti)
    """
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    })
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """
    Декодирование и валидация JWT токена
    
    Raises:
        JWTError: если токен невалиден
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    
    token_type = payload.get("type")
    if token_type != expected_type:
        raise JWTError(f"Неверный тип токена: ожидался {expected_type}, получен {token_type}")
    
    # Проверка срока действия
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
        raise JWTError("Токен истёк")
    
    return payload


def generate_simple_signature(data: Dict[str, Any], user_id: int, secret: str = None) -> Dict[str, Any]:
    """
    Генерация простой электронной подписи по ГК РФ ст. 160
    """
    if secret is None:
        secret = settings.SECRET_KEY
    
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    sig_payload = f"{user_id}:{timestamp}:{canonical}"
    signature = hmac.new(
        secret.encode(),
        sig_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "signature": signature,
        "timestamp": timestamp,
        "algorithm": "HMAC-SHA256",
        "type": "simple_electronic_signature",
        "legal_basis": "ГК РФ ст. 160 (простая электронная подпись)",
        "signer_id": user_id,
    }


def verify_simple_signature(data: Dict[str, Any], signature_data: Dict[str, Any], secret: str = None) -> bool:
    """Проверка простой электронной подписи"""
    if secret is None:
        secret = settings.SECRET_KEY
    
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    sig_payload = f"{signature_data['signer_id']}:{signature_data['timestamp']}:{canonical}"
    expected = hmac.new(
        secret.encode(),
        sig_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature_data["signature"])


def generate_secure_filename(original: str) -> str:
    """Генерация безопасного имени файла"""
    ext = original.split(".")[-1].lower() if "." in original else "bin"
    return f"{secrets.token_urlsafe(16)}.{ext}"


def sanitize_input(value: str, max_length: int = 255) -> str:
    """Санитизация пользовательского ввода"""
    if not value:
        return ""
    # Удаляем потенциально опасные символы
    value = re.sub(r'[<>&"\']', '', value)
    return value[:max_length].strip()


import json


# ============ AUTH DEPENDENCIES ============
# These are here to avoid circular imports between auth.py and other modules
# They are placed at the END of the file and use lazy imports.

from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

# Lazy import to break circular dependency: security.py -> models.py -> database.py -> __init__.py -> security.py
import importlib

def _get_models():
    """Lazy import of models to avoid circular imports."""
    mod = importlib.import_module("app.models")
    return mod.User, mod.UserSession


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Получение текущего пользователя из JWT токена с проверкой jti"""
    User, UserSession = _get_models()
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    token = auth_header[7:]
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        user_id = int(payload.get("sub"))
        
        # Проверка что токен не отозван
        if jti:
            result = await db.execute(
                select(UserSession).where(
                    UserSession.jti == jti,
                    UserSession.revoked == False,
                    UserSession.expires_at > datetime.now(timezone.utc),
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=401, detail="Токен отозван или истёк")
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Пользователь не найден или заблокирован")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Неверный или истёкший токен")


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Опциональная авторизация"""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None

