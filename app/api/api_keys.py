"""
API Keys v7.1
Управление ключами доступа для внешних интеграций
"""

import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


# Хранилище ключей в памяти (в проде — в Redis/БД)
_api_keys: dict = {}


class APIKeyCreate(BaseModel):
    name: str
    expires_days: Optional[int] = 365
    permissions: List[str] = ["read"]  # read, write, admin


class APIKeyOut(BaseModel):
    id: str
    name: str
    prefix: str
    permissions: List[str]
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime


def _hash_key(key: str) -> str:
    """Хеширование ключа для хранения"""
    return hashlib.sha256(key.encode()).hexdigest()


# ============ CRUD ============

@router.get("/")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
):
    """Список API ключей пользователя"""
    user_keys = _api_keys.get(current_user.id, {})
    return {
        "keys": [
            {
                "id": k["id"],
                "name": k["name"],
                "prefix": k["prefix"],
                "permissions": k["permissions"],
                "expires_at": k.get("expires_at"),
                "last_used_at": k.get("last_used_at"),
                "created_at": k["created_at"],
            }
            for k in user_keys.values()
        ]
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Создание нового API ключа"""
    # Проверка лимита ключей
    user_keys = _api_keys.get(current_user.id, {})
    if len(user_keys) >= 10:
        raise HTTPException(status_code=403, detail="Максимум 10 API ключей")

    # Генерация ключа
    key_id = secrets.token_urlsafe(16)
    raw_key = f"msk_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:12]

    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=key_data.expires_days)

    key_record = {
        "id": key_id,
        "name": key_data.name,
        "prefix": prefix,
        "hash": _hash_key(raw_key),
        "permissions": key_data.permissions,
        "expires_at": expires_at,
        "last_used_at": None,
        "created_at": datetime.now(timezone.utc),
    }

    if current_user.id not in _api_keys:
        _api_keys[current_user.id] = {}
    _api_keys[current_user.id][key_id] = key_record

    await log_audit(
        action="api_key_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Key: {key_data.name}",
    )

    # Возвращаем raw_key только один раз
    return {
        "message": "API ключ создан",
        "key_id": key_id,
        "api_key": raw_key,  # Показываем только при создании
        "prefix": prefix,
        "expires_at": expires_at,
    }


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Отзыв API ключа"""
    user_keys = _api_keys.get(current_user.id, {})
    if key_id not in user_keys:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    del user_keys[key_id]

    await log_audit(
        action="api_key_revoked",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Key ID: {key_id}",
    )


# ============ AUTH BY API KEY ============

async def get_user_by_api_key(api_key: str) -> Optional[User]:
    """Получение пользователя по API ключу"""
    if not api_key or not api_key.startswith("msk_"):
        return None

    key_hash = _hash_key(api_key)

    for user_id, keys in _api_keys.items():
        for key_id, key_data in keys.items():
            if key_data["hash"] == key_hash:
                # Проверка срока действия
                if key_data.get("expires_at") and key_data["expires_at"] < datetime.now(timezone.utc):
                    continue

                # Обновление last_used
                key_data["last_used_at"] = datetime.now(timezone.utc)

                # Возвращаем пользователя (в реальном приложении — запрос к БД)
                return None  # Заглушка — нужен запрос к БД

    return None
