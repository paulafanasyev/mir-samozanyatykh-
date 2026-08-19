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
import json

import jwt
from jwt import PyJWTError as JWTError
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

# Fixed-cost dummy bcrypt hash; never generate a new hash on failed login.
DUMMY_PASSWORD_HASH = "$2b$12$C6UzMDM.H6dfI/f/IKcEe.VJ2Qm3bVq3w5dX8nX6QY8b8m4s6mJQe"

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Проверка пароля с защитой от timing attacks"""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        pwd_context.verify(plain, DUMMY_PASSWORD_HASH)
        return False


def get_password_hash(password: str) -> str:
    """Хеширование пароля bcrypt"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Валидация сложности пароля по OWASP рекомендациям
    """
    if len(password) < 12:
        return False, "Пароль должен содержать минимум 12 символов"
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


def create_2fa_pending_token(data: Dict[str, Any]) -> Tuple[str, str]:
    """Create a short-lived token usable only for completing 2FA login."""
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode.update({"exp": expire, "jti": jti, "type": "2fa_pending", "iat": datetime.now(timezone.utc), "nbf": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM), jti


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
    if expected_type == "access" and payload.get("2fa_pending"):
        raise JWTError("2FA pending token cannot access protected resources")
    if not payload.get("sub"):
        raise JWTError("Token subject is required")
    if expected_type == "access" and not payload.get("jti"):
        raise JWTError("Access token jti is required")
    
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
    
    required = {"signature", "timestamp", "signer_id", "algorithm", "type"}
    if not required.issubset(signature_data):
        return False
    if signature_data.get("algorithm") != "HMAC-SHA256" or signature_data.get("type") != "simple_electronic_signature":
        return False
    try:
        signed_at = datetime.fromisoformat(str(signature_data["timestamp"]).replace("Z", "+00:00"))
        if signed_at.tzinfo is None:
            signed_at = signed_at.replace(tzinfo=timezone.utc)
        # A stored signature must not be accepted with an invalid/future timestamp.
        now = datetime.now(timezone.utc)
        if signed_at > now + timedelta(minutes=5):
            return False
    except (TypeError, ValueError):
        return False

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



