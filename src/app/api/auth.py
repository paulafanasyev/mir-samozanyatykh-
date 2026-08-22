"""
API аутентификации: регистрация, вход, выход, refresh, 2FA, OAuth
Мир Самозанятых v7.5
АНО ЦПС ИНН 9724016805
"""

import secrets
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, validate_password_strength,
    validate_email, create_access_token, create_refresh_token, create_2fa_pending_token, decode_token,
    generate_csrf_token, hash_token,
)
from app.core.auth import get_current_user, get_current_user_optional
from app.core.logging import logger, log_audit
from app.models import User, UserSession, UserMFA, AuditLog
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse,
    MFASetupResponse, MFAVerify,
    PasswordChange, PasswordResetRequest, PasswordResetConfirm,
)
from app.services.email import email_service

import pyotp
from app.core.rate_limit import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _is_mobile_client(request: Request) -> bool:
    return request.headers.get("X-Client-Type", "").lower() in {"mobile", "flutter"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ============ REGISTRATION ============

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    email: str = Form(..., max_length=255),
    password: str = Form(..., max_length=128),
    full_name: str = Form(..., max_length=255),
    phone: Optional[str] = Form(None, max_length=50),
    inn: Optional[str] = Form(None, max_length=20),
    referral_code: Optional[str] = Form(None, max_length=64),
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя"""
    email = email.strip().lower()
    if not validate_email(email):
        raise HTTPException(status_code=400, detail="Неверный формат email")
    is_strong, msg = validate_password_strength(password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=msg)
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    verification_token = secrets.token_urlsafe(32)
    new_user = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        phone=phone,
        inn=inn,
        is_verified=False,
        email_verification_token_hash=hash_token(verification_token),
        email_verification_expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    referral_code = (referral_code or request.query_params.get("ref"))
    if referral_code:
        from app.api.referrals import generate_referral_code
        ref_result = await db.execute(select(User).where(User.referral_code == referral_code.upper().strip()))
        referrer = ref_result.scalar_one_or_none()
        if referrer and referrer.id != new_user.id:
            from app.models import Referral
            from app.api.referrals import REFERRAL_REWARDS, get_referral_level
            from decimal import Decimal
            level = get_referral_level(referrer.referral_count or 0)
            reward = REFERRAL_REWARDS["registration"]
            bonus = reward * Decimal(level["bonus_pct"]) / Decimal("100")
            total_reward = reward + bonus
            referral = Referral(referrer_id=referrer.id, referred_id=new_user.id, status="registered", reward_amount=total_reward)
            db.add(referral)
            new_user.referred_by = referrer.id
            referrer.referral_count = (referrer.referral_count or 0) + 1
            referrer.points = (referrer.points or 0) + 50
            from app.models import Notification
            db.add(Notification(user_id=referrer.id, title="Новый реферал!", body=f"{new_user.full_name or new_user.email} зарегистрировался по вашей ссылке. +{float(total_reward)} руб.", notification_type="success"))
            await db.commit()
    if not new_user.referral_code:
        from app.api.referrals import generate_referral_code
        new_user.referral_code = generate_referral_code()
        await db.commit()
    email_sent = await email_service.send_verification(email, verification_token)
    await log_audit(action="register", user_id=new_user.id, ip_address=request.client.host, details=f"Registration, email_sent={email_sent}, ref={referral_code}")
    return {"message": "Регистрация успешна. Проверьте email.", "email_sent": email_sent, "user_id": new_user.id}


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Подтверждение email"""
    now = datetime.now(timezone.utc)
    result = await db.execute(select(User).where(User.email_verification_token_hash == hash_token(token), User.email_verification_expires_at > now))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Неверный или истёкший токен")
    user.is_verified = True
    user.email_verified_at = now
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    await db.commit()
    await log_audit(action="email_verified", user_id=user.id)
    return {"message": "Email успешно подтверждён!"}


# ============ LOGIN / LOGOUT ============

@router.post("/login", response_model=TokenResponse)
@limiter.limit('5/minute')
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Вход в систему с блокировкой после 5 попыток"""
    email = email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=f"Аккаунт заблокирован. Попробуйте через {remaining} минут.")
    if not user or not verify_password(password, user.password_hash):
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
            await db.commit()
        await log_audit(action="login_failed", user_id=user.id if user else None, ip_address=request.client.host, details=f"Failed login for {email}", success=False)
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Подтвердите email перед входом")
    # Remaining login/MFA/OAuth handlers continue below in the repository.
