"""
API аутентификации: регистрация, вход, выход, refresh, 2FA, OAuth
Мир Самозанятых v7.5
АНО ЦПС ИНН 9724016805
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, validate_password_strength,
    validate_email, create_access_token, create_refresh_token, decode_token,
    generate_csrf_token, get_current_user, get_current_user_optional,
)
from app.core.logging import logger, log_audit
from app.models import User, UserSession, UserMFA, AuditLog
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse,
    MFASetupResponse, MFAVerify,
    PasswordChange, PasswordResetRequest, PasswordResetConfirm,
)
from app.services.email import email_service

import pyotp

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ============ REGISTRATION ============

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    email: str = Form(..., max_length=255),
    password: str = Form(..., max_length=128),
    full_name: str = Form(..., max_length=255),
    phone: Optional[str] = Form(None, max_length=50),
    inn: Optional[str] = Form(None, max_length=20),
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя"""
    # Валидация email
    if not validate_email(email):
        raise HTTPException(status_code=400, detail="Неверный формат email")
    
    # Валидация пароля
    is_strong, msg = validate_password_strength(password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=msg)
    
    # Проверка уникальности
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    
    # Создание пользователя
    verification_token = secrets.token_urlsafe(32)
    new_user = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name,
        phone=phone,
        inn=inn,
        is_verified=False,
        email_verification_token=verification_token,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Отправка email
    email_sent = await email_service.send_verification(email, verification_token)
    
    await log_audit(
        action="register",
        user_id=new_user.id,
        ip_address=request.client.host,
        details=f"Registration, email_sent={email_sent}",
    )
    
    return {
        "message": "Регистрация успешна. Проверьте email.",
        "email_sent": email_sent,
        "user_id": new_user.id,
    }


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Подтверждение email"""
    result = await db.execute(
        select(User).where(User.email_verification_token == token)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Неверный или истёкший токен")
    
    user.is_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.email_verification_token = None
    await db.commit()
    
    await log_audit(action="email_verified", user_id=user.id)
    return {"message": "Email успешно подтверждён!"}


# ============ LOGIN / LOGOUT ============

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Вход в систему с блокировкой после 5 попыток"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    # Проверка блокировки
    if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Аккаунт заблокирован. Попробуйте через {remaining} минут.",
        )
    
    # Проверка пароля
    if not user or not verify_password(password, user.password_hash):
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.LOGIN_LOCKOUT_MINUTES
                )
            await db.commit()
        
        await log_audit(
            action="login_failed",
            user_id=user.id if user else None,
            ip_address=request.client.host,
            details=f"Failed login for {email}",
            success=False,
        )
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    # Проверка верификации
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Подтвердите email перед входом")
    
    # Проверка 2FA
    mfa_result = await db.execute(select(UserMFA).where(UserMFA.user_id == user.id))
    mfa = mfa_result.scalar_one_or_none()
    if mfa and mfa.is_enabled:
        # Требуется 2FA код
        return {
            "requires_2fa": True,
            "temp_token": create_access_token(
                {"sub": str(user.id), "email": user.email, "2fa_pending": True},
                expires_delta=timedelta(minutes=5),
            )[0],
        }
    
    # Сброс счётчика попыток
    user.failed_login_attempts = 0
    user.locked_until = None
    
    # Создание токенов
    access_token, access_jti = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token, refresh_jti = create_refresh_token({"sub": str(user.id)})
    
    now = datetime.now(timezone.utc)
    db.add_all([
        UserSession(
            user_id=user.id,
            jti=access_jti,
            token_type="access",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        UserSession(
            user_id=user.id,
            jti=refresh_jti,
            token_type="refresh",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ),
    ])
    await db.commit()
    
    await log_audit(
        action="login",
        user_id=user.id,
        ip_address=request.client.host,
        details="Successful login",
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        tier=user.subscription_tier,
    )


@router.post("/login/2fa")
async def login_2fa(
    request: Request,
    temp_token: str = Form(...),
    code: str = Form(..., min_length=6, max_length=6),
    db: AsyncSession = Depends(get_db),
):
    """Вход с 2FA кодом"""
    try:
        payload = decode_token(temp_token, expected_type="access")
        if not payload.get("2fa_pending"):
            raise HTTPException(status_code=400, detail="Неверный временный токен")
    except Exception:
        raise HTTPException(status_code=401, detail="Неверный или истёкший токен")
    
    user_id = int(payload["sub"])
    result = await db.execute(select(UserMFA).where(UserMFA.user_id == user_id))
    mfa = result.scalar_one_or_none()
    
    if not mfa or not mfa.is_enabled:
        raise HTTPException(status_code=400, detail="2FA не настроен")
    
    totp = pyotp.TOTP(mfa.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Неверный код 2FA")
    
    # Создание полноценных токенов
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    access_token, access_jti = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token, refresh_jti = create_refresh_token({"sub": str(user.id)})
    
    now = datetime.now(timezone.utc)
    db.add_all([
        UserSession(
            user_id=user.id, jti=access_jti, token_type="access",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ),
        UserSession(
            user_id=user.id, jti=refresh_jti, token_type="refresh",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ),
    ])
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        tier=user.subscription_tier,
    )


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Выход из системы (отзыв токена)"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            user_id = int(payload.get("sub"))
            if jti:
                await db.execute(
                    update(UserSession)
                    .where(UserSession.jti == jti)
                    .values(revoked=True)
                )
                await db.commit()
            await log_audit(action="logout", user_id=user_id)
        except Exception as e:
            logger.warning(f"Logout token error: {e}")
    
    return {"message": "Выход выполнен успешно"}


@router.post("/refresh")
async def refresh_token(
    request: Request,
    refresh_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Обновление access token через refresh token"""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        jti = payload.get("jti")
        user_id = int(payload.get("sub"))
        
        # Проверка что refresh token не отозван
        result = await db.execute(
            select(UserSession).where(
                UserSession.jti == jti,
                UserSession.revoked == False,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=401, detail="Refresh token отозван или истёк")
        
        # Отзыв старого refresh token
        await db.execute(
            update(UserSession).where(UserSession.jti == jti).values(revoked=True)
        )
        
        # Создание новых токенов
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        
        new_access, new_access_jti = create_access_token({"sub": str(user.id), "email": user.email})
        new_refresh, new_refresh_jti = create_refresh_token({"sub": str(user.id)})
        
        now = datetime.now(timezone.utc)
        db.add_all([
            UserSession(
                user_id=user.id, jti=new_access_jti, token_type="access",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            ),
            UserSession(
                user_id=user.id, jti=new_refresh_jti, token_type="refresh",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ),
        ])
        await db.commit()
        
        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            tier=user.subscription_tier,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=401, detail="Неверный refresh token")


# ============ 2FA ============

@router.post("/2fa/setup")
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Настройка 2FA (TOTP)"""
    result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id))
    mfa = result.scalar_one_or_none()
    if mfa and mfa.is_enabled:
        raise HTTPException(status_code=400, detail="2FA уже включен")
    
    secret = pyotp.random_base32()
    backup_codes = [secrets.token_hex(4) for _ in range(8)]
    hashed_backups = __import__("json").dumps([get_password_hash(code) for code in backup_codes])
    
    if not mfa:
        mfa = UserMFA(
            user_id=current_user.id,
            totp_secret=secret,
            backup_codes=hashed_backups,
        )
        db.add(mfa)
    else:
        mfa.totp_secret = secret
        mfa.backup_codes = hashed_backups
        mfa.is_enabled = False
    
    await db.commit()
    await db.refresh(mfa)
    
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=current_user.email or str(current_user.id),
        issuer_name="Мир Самозанятых",
    )
    
    # QR код
    import qrcode
    import io
    import base64
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    return MFASetupResponse(
        qr_code=f"data:image/png;base64,{qr_b64}",
        secret=secret,
        backup_codes=backup_codes,
        message="Сохраните резервные коды! Они показываются только один раз.",
    )


@router.post("/2fa/verify")
async def verify_2fa_setup(
    code: str = Form(..., min_length=6, max_length=6),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Подтверждение настройки 2FA"""
    result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id))
    mfa = result.scalar_one_or_none()
    if not mfa:
        raise HTTPException(status_code=400, detail="2FA не настроен")
    if mfa.is_enabled:
        raise HTTPException(status_code=400, detail="2FA уже включен")
    
    totp = pyotp.TOTP(mfa.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=400, detail="Неверный TOTP код")
    
    mfa.is_enabled = True
    await db.commit()
    await log_audit(action="2fa_enabled", user_id=current_user.id, resource="user_mfa")
    return {"message": "2FA успешно включён"}


@router.post("/2fa/disable")
async def disable_2fa(
    password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отключение 2FA"""
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(status_code=403, detail="Неверный пароль")
    
    result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id))
    mfa = result.scalar_one_or_none()
    if not mfa or not mfa.is_enabled:
        raise HTTPException(status_code=400, detail="2FA не включен")
    
    mfa.is_enabled = False
    mfa.totp_secret = ""
    mfa.backup_codes = "[]"
    await db.commit()
    await log_audit(action="2fa_disabled", user_id=current_user.id, resource="user_mfa")
    return {"message": "2FA отключён"}


# ============ PASSWORD RESET ============

@router.post("/password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Запрос сброса пароля"""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    # Всегда возвращаем одинаковый ответ для защиты от перечисления email
    if user:
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token  # переиспользуем поле для reset token
        await db.commit()
        await email_service.send_password_reset(user.email, token)
    
    return {"message": "Если email зарегистрирован, вы получите письмо со ссылкой для сброса пароля"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Подтверждение сброса пароля"""
    result = await db.execute(
        select(User).where(User.email_verification_token == request.token)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Неверный или истёкший токен")
    
    user.password_hash = get_password_hash(request.new_password)
    user.email_verification_token = None
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()
    
    # Отзыв всех сессий
    await db.execute(
        update(UserSession).where(UserSession.user_id == user.id).values(revoked=True)
    )
    await db.commit()
    
    await log_audit(action="password_reset", user_id=user.id)
    return {"message": "Пароль успешно изменён"}
