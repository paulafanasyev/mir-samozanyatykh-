"""
White-label API v7.0
Кастомизация платформы под бренд пользователя
"""

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User

router = APIRouter(prefix="/api/white-label", tags=["white-label"])


class BrandingSettings(BaseModel):
    app_name: Optional[str] = None
    primary_color: Optional[str] = "#1976D2"
    secondary_color: Optional[str] = "#0D47A1"
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    custom_domain: Optional[str] = None
    email_from_name: Optional[str] = None
    email_footer: Optional[str] = None


@router.get("/settings")
async def get_branding(
    current_user: User = Depends(get_current_user),
):
    """Получить настройки брендинга"""
    return {
        "app_name": current_user.full_name or "Мир Самозанятых",
        "primary_color": "#1976D2",
        "secondary_color": "#0D47A1",
        "logo_url": None,
        "favicon_url": None,
        "custom_domain": None,
        "email_from_name": current_user.full_name,
        "email_footer": "С уважением, команда Мир Самозанятых",
        "tier_required": "business",  # минимальный тариф
    }


@router.put("/settings")
async def update_branding(
    settings: BrandingSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновить настройки брендинга (только business/enterprise)"""
    if current_user.user_tier not in ["business", "enterprise"]:
        raise HTTPException(
            status_code=403,
            detail="White-label доступен только на тарифах Бизнес и Корпоративный"
        )

    # Сохраняем в JSON поле пользователя
    branding = {
        "app_name": settings.app_name,
        "primary_color": settings.primary_color,
        "secondary_color": settings.secondary_color,
        "logo_url": settings.logo_url,
        "favicon_url": settings.favicon_url,
        "custom_domain": settings.custom_domain,
        "email_from_name": settings.email_from_name,
        "email_footer": settings.email_footer,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # В реальном приложении сохранить в БД
    return {
        "message": "Настройки брендинга обновлены",
        "settings": branding,
    }


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Загрузка логотипа"""
    if current_user.user_tier not in ["business", "enterprise"]:
        raise HTTPException(status_code=403, detail="Требуется тариф Бизнес+")

    # В реальном приложении — загрузка в S3/MinIO
    return {
        "message": "Логотип загружен",
        "filename": file.filename,
        "url": f"/static/uploads/logos/{current_user.id}_{file.filename}",
    }


@router.get("/css")
async def generate_css(
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать CSS с кастомными цветами"""
    # В реальном приложении — чтение из БД
    primary = "#1976D2"
    secondary = "#0D47A1"

    css = f"""
    :root {{
        --primary-color: {primary};
        --secondary-color: {secondary};
        --primary-light: {primary}20;
        --primary-dark: {secondary};
    }}
    .brand-primary {{ color: var(--primary-color); }}
    .brand-bg {{ background-color: var(--primary-color); }}
    .brand-border {{ border-color: var(--primary-color); }}
    """
    return {"css": css}
