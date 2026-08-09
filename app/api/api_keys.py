"""
API ключи v7.9
Генерация, управление, scopes, rate limiting
АНО ЦПС ИНН 9724016805
"""

import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User, ApiKey

router = APIRouter(prefix="/api/api-keys", tags=["api_keys"])


# ============ SCHEMAS ============

class ApiKeyCreate(BaseModel):
    name: str = Field(..., max_length=100)
    scopes: List[str] = Field(default=["read"])
    expires_days: Optional[int] = Field(365, ge=1, le=1095)


class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    scopes: List[str]
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyWithSecret(BaseModel):
    id: int
    name: str
    key: str  # plain key, shown ONLY once on creation
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[datetime]
    created_at: datetime


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    scopes: Optional[List[str]] = None
    is_active: Optional[bool] = None


# ============ HELPERS ============

def generate_api_key() -> str:
    """Генерация случайного API ключа: ms_ + 48 hex chars"""
    return "ms_" + secrets.token_hex(24)


def hash_key(key: str) -> str:
    """SHA-256 хеш ключа для хранения"""
    return hashlib.sha256(key.encode()).hexdigest()


def get_key_prefix(key: str) -> str:
    """Первые 8 символов для отображения"""
    return key[:8]


# ============ ENDPOINTS ============

@router.post("/", response_model=ApiKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ApiKeyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание нового API ключа. Ключ показывается ТОЛЬКО один раз!"""
    # Лимит ключей на пользователя
    count = await db.scalar(
        select(func.count(ApiKey.id)).where(
            ApiKey.user_id == current_user.id,
            ApiKey.is_active == True,
        )
    )
    if count >= 10:
        raise HTTPException(status_code=400, detail="Максимум 10 активных ключей")

    plain_key = generate_api_key()
    key_hash = hash_key(plain_key)
    prefix = get_key_prefix(plain_key)

    expires_at = None
    if data.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_days)

    api_key = ApiKey(
        user_id=current_user.id,
        name=data.name,
        key_hash=key_hash,
        key_prefix=prefix,
        scopes=data.scopes,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    await log_audit(
        action="api_key_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Key {api_key.id} created",
    )

    return ApiKeyWithSecret(
        id=api_key.id,
        name=api_key.name,
        key=plain_key,
        key_prefix=prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.get("/", response_model=List[ApiKeyOut])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список API ключей пользователя (без секретов)"""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [ApiKeyOut.model_validate(k) for k in keys]


@router.put("/{key_id}", response_model=ApiKeyOut)
async def update_api_key(
    key_id: int,
    update: ApiKeyUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление API ключа (name, scopes, active)"""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(api_key, key, value)

    await db.commit()
    await db.refresh(api_key)

    await log_audit(
        action="api_key_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Key {key_id} updated",
    )
    return ApiKeyOut.model_validate(api_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отзыв (удаление) API ключа"""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="Ключ не найден")

    await db.delete(api_key)
    await db.commit()

    await log_audit(
        action="api_key_deleted",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Key {key_id} deleted",
    )
