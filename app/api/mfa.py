"""
2FA / MFA API v7.0
Двухфакторная аутентификация через TOTP
"""

import pyotp
import qrcode
import io
import base64
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, UserMFA

router = APIRouter(prefix="/api/mfa", tags=["mfa"])


class MFAToggle(BaseModel):
    enabled: bool


class MFAVerify(BaseModel):
    code: str


@router.get("/status")
async def mfa_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Статус 2FA"""
    result = await db.execute(
        select(UserMFA).where(UserMFA.user_id == current_user.id)
    )
    mfa = result.scalar_one_or_none()

    return {
        "enabled": mfa.is_enabled if mfa else False,
        "has_secret": bool(mfa and mfa.totp_secret),
        "backup_codes_count": len(json.loads(mfa.backup_codes)) if mfa and mfa.backup_codes else 0,
    }


@router.post("/setup")
async def setup_mfa(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Настройка 2FA — генерация секрета и QR-кода"""
    # Генерация секрета
    secret = pyotp.random_base32()

    # Создание или обновление MFA записи
    result = await db.execute(
        select(UserMFA).where(UserMFA.user_id == current_user.id)
    )
    mfa = result.scalar_one_or_none()

    if not mfa:
        import json
        mfa = UserMFA(
            user_id=current_user.id,
            totp_secret=secret,
            backup_codes=json.dumps([]),
            is_enabled=False,
        )
        db.add(mfa)
    else:
        mfa.totp_secret = secret
        mfa.is_enabled = False

    await db.commit()

    # Генерация QR-кода
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Мир Самозанятых"
    )

    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "manual_entry": secret,
        "message": "Отсканируйте QR-код в Google Authenticator или аналогичном приложении",
    }


@router.post("/verify-and-enable")
async def verify_and_enable_mfa(
    verify: MFAVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Подтверждение кода и включение 2FA"""
    result = await db.execute(
        select(UserMFA).where(UserMFA.user_id == current_user.id)
    )
    mfa = result.scalar_one_or_none()

    if not mfa or not mfa.totp_secret:
        raise HTTPException(status_code=400, detail="Сначала настройте 2FA через /setup")

    totp = pyotp.TOTP(mfa.totp_secret)
    if not totp.verify(verify.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Неверный код подтверждения")

    # Генерация backup codes
    import json, secrets
    backup_codes = [secrets.token_hex(4) for _ in range(8)]
    mfa.backup_codes = json.dumps(backup_codes)
    mfa.is_enabled = True

    await db.commit()

    return {
        "message": "2FA успешно включена",
        "backup_codes": backup_codes,
        "warning": "Сохраните backup codes в надёжном месте!",
    }


@router.post("/verify")
async def verify_mfa_code(
    verify: MFAVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Проверка MFA кода при входе"""
    result = await db.execute(
        select(UserMFA).where(UserMFA.user_id == current_user.id)
    )
    mfa = result.scalar_one_or_none()

    if not mfa or not mfa.is_enabled:
        return {"valid": True, "message": "2FA не включена"}

    totp = pyotp.TOTP(mfa.totp_secret)

    # Проверка TOTP кода
    if totp.verify(verify.code, valid_window=1):
        return {"valid": True, "message": "Код подтверждён"}

    # Проверка backup code
    import json
    backup_codes = json.loads(mfa.backup_codes or "[]")
    if verify.code in backup_codes:
        backup_codes.remove(verify.code)
        mfa.backup_codes = json.dumps(backup_codes)
        await db.commit()
        return {"valid": True, "message": "Использован backup code"}

    raise HTTPException(status_code=400, detail="Неверный код")


@router.post("/disable")
async def disable_mfa(
    verify: MFAVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отключение 2FA"""
    result = await db.execute(
        select(UserMFA).where(UserMFA.user_id == current_user.id)
    )
    mfa = result.scalar_one_or_none()

    if not mfa or not mfa.is_enabled:
        return {"message": "2FA уже отключена"}

    totp = pyotp.TOTP(mfa.totp_secret)
    if not totp.verify(verify.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Неверный код для отключения 2FA")

    mfa.is_enabled = False
    await db.commit()

    return {"message": "2FA отключена"}
