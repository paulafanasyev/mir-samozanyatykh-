"""
Аутентификация: get_current_user, get_current_user_optional
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.core.logging import logger

# Lazy import to avoid circular dependency
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
