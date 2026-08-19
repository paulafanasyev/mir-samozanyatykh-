"""
White-label API v7.0
Кастомизация платформы под бренд пользователя
"""

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.core.auth import get_current_user, get_current_user_optional
from app.core.file_security import validate_upload, read_limited, private_storage_path

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
    """Получить сохранённые настройки брендинга."""
    branding = dict(current_user.branding_settings or {})
    defaults = {
        "app_name": current_user.full_name or "Мир Самозанятых",
        "primary_color": "#1976D2",
        "secondary_color": "#0D47A1",
        "logo_url": None,
        "favicon_url": None,
        "custom_domain": None,
        "email_from_name": current_user.full_name,
        "email_footer": "С уважением, команда Мир Самозанятых",
    }
    defaults.update(branding)
    defaults["tier_required"] = "business"
    return defaults


def _validate_color(value: Optional[str], field_name: str) -> Optional[str]:
    if value is None:
        return None
    import re
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise HTTPException(status_code=422, detail=f"{field_name}: требуется цвет в формате #RRGGBB")
    return value.upper()


@router.put("/settings")
async def update_branding(
    branding_settings: BrandingSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сохранить настройки брендинга в БД."""
    if current_user.user_tier not in ["business", "enterprise"]:
        raise HTTPException(status_code=403, detail="White-label доступен только на тарифах Бизнес и Корпоративный")

    primary = _validate_color(branding_settings.primary_color, "primary_color") or "#1976D2"
    secondary = _validate_color(branding_settings.secondary_color, "secondary_color") or "#0D47A1"
    custom_domain = (branding_settings.custom_domain or "").strip() or None
    if custom_domain and ("/" in custom_domain or " " in custom_domain or "://" in custom_domain):
        raise HTTPException(status_code=422, detail="custom_domain должен быть только hostname")

    branding = {
        "app_name": (branding_settings.app_name or current_user.full_name or "Мир Самозанятых").strip()[:255],
        "primary_color": primary,
        "secondary_color": secondary,
        "logo_url": branding_settings.logo_url,
        "favicon_url": branding_settings.favicon_url,
        "custom_domain": custom_domain,
        "email_from_name": (branding_settings.email_from_name or current_user.full_name or "Мир Самозанятых").strip()[:255],
        "email_footer": (branding_settings.email_footer or "С уважением, команда Мир Самозанятых")[:2000],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    current_user.branding_settings = branding
    await db.commit()
    await db.refresh(current_user)
    return {"message": "Настройки брендинга обновлены", "settings": {**branding, "tier_required": "business"}}


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Загрузка логотипа"""
    if current_user.user_tier not in ["business", "enterprise"]:
        raise HTTPException(status_code=403, detail="Требуется тариф Бизнес+")

    ext = validate_upload(file.filename, file.content_type, {".png", ".jpg", ".jpeg", ".webp"})
    content = await read_limited(file, 2 * 1024 * 1024)
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        signatures = {".png": b"\x89PNG\r\n\x1a\n", ".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff", ".webp": b"RIFF"}
        if not content.startswith(signatures[ext]):
            raise HTTPException(status_code=400, detail="Содержимое изображения не соответствует расширению")
    path = private_storage_path("logos", file.filename or "logo", current_user.id)
    Path(path).write_bytes(content)
    return {"message": "Логотип загружен", "filename": Path(path).name, "url": f"/api/white-label/logo/{Path(path).name}"}


@router.get("/logo/{filename}")
async def get_logo(filename: str, current_user: User = Depends(get_current_user)):
    from fastapi.responses import FileResponse
    path = Path("data/private/logos") / filename
    resolved = path.resolve()
    root = Path("data/private/logos").resolve()
    if root not in resolved.parents or resolved.name != filename or not resolved.is_file():
        raise HTTPException(status_code=404, detail="Логотип не найден")
    if not resolved.name.startswith(f"{current_user.id}_"):
        raise HTTPException(status_code=403, detail="Нет доступа к файлу")
    return FileResponse(str(resolved))


@router.get("/css")
async def generate_css(
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать CSS с кастомными цветами"""
    branding = dict(current_user.branding_settings or {})
    primary = branding.get("primary_color", "#1976D2")
    secondary = branding.get("secondary_color", "#0D47A1")

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
