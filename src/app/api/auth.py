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
    mfa_result = await db.execute(select(UserMFA).where(UserMFA.user_id == user.id))
    mfa = mfa_result.scalar_one_or_none()
    if mfa and mfa.is_enabled:
        return {"requires_2fa": True, "temp_token": create_2fa_pending_token({"sub": str(user.id), "email": user.email})[0]}
    user.failed_login_attempts = 0
    user.locked_until = None
    access_token, access_jti = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token, refresh_jti = create_refresh_token({"sub": str(user.id)})
    now = datetime.now(timezone.utc)
    db.add_all([
        UserSession(user_id=user.id, jti=access_jti, token_type="access", ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""), expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        UserSession(user_id=user.id, jti=refresh_jti, token_type="refresh", ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""), expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)),
    ])
    await db.commit()
    await log_audit(action="login", user_id=user.id, ip_address=request.client.host, details="Successful login")
    csrf_token = generate_csrf_token()
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=settings.ENVIRONMENT == "production", samesite="strict", path="/api/auth/refresh", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    response.set_cookie("csrf_token", csrf_token, httponly=False, secure=settings.ENVIRONMENT == "production", samesite="strict", path="/", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token if _is_mobile_client(request) else None, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, tier=user.subscription_tier)


@router.post("/login/2fa")
@limiter.limit('3/minute')
async def login_2fa(request: Request, response: Response, temp_token: str = Form(...), code: str = Form(..., min_length=6, max_length=6), db: AsyncSession = Depends(get_db)):
    """Вход с 2FA кодом"""
    try:
        payload = decode_token(temp_token, expected_type="2fa_pending")
        if payload.get("type") != "2fa_pending": raise HTTPException(status_code=400, detail="Неверный временный токен")
    except Exception: raise HTTPException(status_code=401, detail="Неверный или истёкший токен")
    user_id = int(payload["sub"])
    result = await db.execute(select(UserMFA).where(UserMFA.user_id == user_id)); mfa = result.scalar_one_or_none()
    if not mfa or not mfa.is_enabled: raise HTTPException(status_code=400, detail="2FA не настроен")
    totp = pyotp.TOTP(mfa.totp_secret); valid = totp.verify(code, valid_window=1)
    if not valid:
        backup_codes = json.loads(mfa.backup_codes or "[]")
        for index, code_hash in enumerate(backup_codes):
            if verify_password(code, code_hash):
                backup_codes.pop(index); mfa.backup_codes = json.dumps(backup_codes); await db.commit(); valid = True; await log_audit(action="2fa_backup_code_used", user_id=user_id); break
    if not valid: raise HTTPException(status_code=401, detail="Неверный код 2FA")
    result = await db.execute(select(User).where(User.id == user_id)); user = result.scalar_one()
    access_token, access_jti = create_access_token({"sub": str(user.id), "email": user.email}); refresh_token, refresh_jti = create_refresh_token({"sub": str(user.id)})
    now = datetime.now(timezone.utc)
    db.add_all([UserSession(user_id=user.id, jti=access_jti, token_type="access", ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""), expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)), UserSession(user_id=user.id, jti=refresh_jti, token_type="refresh", ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""), expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))]); await db.commit()
    csrf_token = generate_csrf_token(); response.set_cookie("refresh_token", refresh_token, httponly=True, secure=settings.ENVIRONMENT == "production", samesite="strict", path="/api/auth/refresh", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400); response.set_cookie("csrf_token", csrf_token, httponly=False, secure=settings.ENVIRONMENT == "production", samesite="strict", path="/", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token if _is_mobile_client(request) else None, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, tier=user.subscription_tier)


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Выход из системы (отзыв токена)"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = decode_token(token); jti = payload.get("jti"); user_id = int(payload.get("sub"))
            if jti: await db.execute(update(UserSession).where(UserSession.jti == jti).values(revoked=True)); await db.commit()
            await log_audit(action="logout", user_id=user_id)
        except Exception as e: logger.warning(f"Logout token error: {e}")
    response.delete_cookie("refresh_token", path="/api/auth/refresh"); response.delete_cookie("csrf_token", path="/")
    return {"message": "Выход выполнен успешно"}


@router.post("/refresh")
@limiter.limit('10/minute')
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Обновление access token через refresh token"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token and _is_mobile_client(request):
        try: refresh_token = (await request.json()).get("refresh_token")
        except Exception: refresh_token = None
    if not refresh_token: raise HTTPException(status_code=401, detail="Refresh token отсутствует")
    try:
        payload = decode_token(refresh_token, expected_type="refresh"); jti = payload.get("jti"); user_id = int(payload.get("sub"))
        result = await db.execute(select(UserSession).where(UserSession.jti == jti).with_for_update()); session = result.scalar_one_or_none()
        if not session or session.token_type != "refresh" or session.expires_at <= datetime.now(timezone.utc): raise HTTPException(status_code=401, detail="Refresh token отозван или истёк")
        if session.revoked:
            await db.execute(update(UserSession).where(UserSession.user_id == user_id, UserSession.token_type == "refresh").values(revoked=True)); await db.commit(); raise HTTPException(status_code=401, detail="Обнаружено повторное использование refresh token")
        await db.execute(update(UserSession).where(UserSession.jti == jti).values(revoked=True))
        result = await db.execute(select(User).where(User.id == user_id)); user = result.scalar_one()
        new_access, new_access_jti = create_access_token({"sub": str(user.id), "email": user.email}); new_refresh, new_refresh_jti = create_refresh_token({"sub": str(user.id)})
        now = datetime.now(timezone.utc)
        db.add_all([UserSession(user_id=user.id, jti=new_access_jti, token_type="access", ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""), expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)), UserSession(user_id=user.id, jti=new_refresh_jti, token_type="refresh", ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""), expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))]); await db.commit()
        csrf_token = generate_csrf_token()
        if not _is_mobile_client(request):
            response.set_cookie("refresh_token", new_refresh, httponly=True, secure=settings.ENVIRONMENT == "production", samesite="strict", path="/api/auth/refresh", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400); response.set_cookie("csrf_token", csrf_token, httponly=False, secure=settings.ENVIRONMENT == "production", samesite="strict", path="/", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
        return TokenResponse(access_token=new_access, refresh_token=new_refresh if _is_mobile_client(request) else None, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, tier=user.subscription_tier)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Refresh error: {e}"); raise HTTPException(status_code=401, detail="Неверный refresh token")


# ============ 2FA ============

@router.post("/2fa/setup")
async def setup_2fa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Настройка 2FA (TOTP)"""
    result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id)); mfa = result.scalar_one_or_none()
    if mfa and mfa.is_enabled: raise HTTPException(status_code=400, detail="2FA уже включен")
    secret = pyotp.random_base32(); backup_codes = [secrets.token_hex(4) for _ in range(8)]; hashed_backups = json.dumps([get_password_hash(code) for code in backup_codes])
    if not mfa: mfa = UserMFA(user_id=current_user.id, totp_secret=secret, backup_codes=hashed_backups); db.add(mfa)
    else: mfa.totp_secret = secret; mfa.backup_codes = hashed_backups; mfa.is_enabled = False
    await db.commit(); await db.refresh(mfa)
    totp = pyotp.TOTP(secret); uri = totp.provisioning_uri(name=current_user.email or str(current_user.id), issuer_name="Мир Самозанятых")
    import qrcode, io, base64
    qr = qrcode.QRCode(version=1, box_size=10, border=5); qr.add_data(uri); qr.make(fit=True); img = qr.make_image(fill_color="black", back_color="white"); buffer = io.BytesIO(); img.save(buffer, format="PNG"); buffer.seek(0); qr_b64 = base64.b64encode(buffer.getvalue()).decode()
    return MFASetupResponse(qr_code=f"data:image/png;base64,{qr_b64}", secret=secret, backup_codes=backup_codes, message="Сохраните резервные коды! Они показываются только один раз.")


@router.post("/2fa/verify")
async def verify_2fa_setup(code: str = Form(..., min_length=6, max_length=6), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Подтверждение настройки 2FA"""
    result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id)); mfa = result.scalar_one_or_none()
    if not mfa: raise HTTPException(status_code=400, detail="2FA не настроен")
    if mfa.is_enabled: raise HTTPException(status_code=400, detail="2FA уже включен")
    totp = pyotp.TOTP(mfa.totp_secret)
    if not totp.verify(code, valid_window=1): raise HTTPException(status_code=400, detail="Неверный TOTP код")
    mfa.is_enabled = True; await db.commit(); await log_audit(action="2fa_enabled", user_id=current_user.id, resource="user_mfa"); return {"message": "2FA успешно включён"}


@router.post("/2fa/disable")
async def disable_2fa(password: str = Form(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Отключение 2FA"""
    if not verify_password(password, current_user.password_hash): raise HTTPException(status_code=403, detail="Неверный пароль")
    result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id)); mfa = result.scalar_one_or_none()
    if not mfa or not mfa.is_enabled: raise HTTPException(status_code=400, detail="2FA не включен")
    mfa.is_enabled = False; mfa.totp_secret = ""; mfa.backup_codes = "[]"; await db.commit(); await log_audit(action="2fa_disabled", user_id=current_user.id, resource="user_mfa"); return {"message": "2FA отключён"}


# ============ PASSWORD RESET ============

@router.post("/password-reset")
async def request_password_reset(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    request.email = request.email.strip().lower(); result = await db.execute(select(User).where(User.email == request.email)); user = result.scalar_one_or_none()
    if user:
        token = secrets.token_urlsafe(32); now = datetime.now(timezone.utc); user.password_reset_token_hash = hash_token(token); user.password_reset_created_at = now; user.password_reset_expires_at = now + timedelta(minutes=15); await db.commit(); await email_service.send_password_reset(user.email, token)
    return {"message": "Если email зарегистрирован, вы получите письмо со ссылкой для сброса пароля"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    is_strong, msg = validate_password_strength(request.new_password)
    if not is_strong: raise HTTPException(status_code=400, detail=msg)
    now = datetime.now(timezone.utc); result = await db.execute(select(User).where(User.password_reset_token_hash == hash_token(request.token), User.password_reset_expires_at > now)); user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=400, detail="Неверный или истёкший токен")
    user.password_hash = get_password_hash(request.new_password); user.password_reset_token_hash = None; user.password_reset_expires_at = None; user.password_reset_created_at = None; user.failed_login_attempts = 0; user.locked_until = None
    await db.execute(update(UserSession).where(UserSession.user_id == user.id).values(revoked=True)); await db.commit(); await log_audit(action="password_reset", user_id=user.id); return {"message": "Пароль успешно изменён"}
