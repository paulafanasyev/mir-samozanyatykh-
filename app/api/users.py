"""
API пользователей: профиль, обновление, удаление
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_password_hash, verify_password
from app.core.logging import log_audit
from app.models import User
from app.schemas.user import UserOut, UserUpdate, PasswordChange

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Получение профиля текущего пользователя"""
    return current_user


@router.put("/me", response_model=UserOut)
async def update_me(
    update: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление профиля"""
    update_data = update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    await log_audit(
        action="profile_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
    )
    return current_user


@router.post("/me/password")
async def change_password(
    data: PasswordChange,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Смена пароля"""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=403, detail="Неверный текущий пароль")
    
    current_user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    
    await log_audit(
        action="password_changed",
        user_id=current_user.id,
        ip_address=request.client.host,
    )
    return {"message": "Пароль успешно изменён"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление аккаунта (GDPR)"""
    await db.delete(current_user)
    await db.commit()
    
    await log_audit(
        action="account_deleted",
        user_id=current_user.id,
        ip_address=request.client.host,
    )
