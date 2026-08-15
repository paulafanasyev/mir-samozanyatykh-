"""
Auth API for Mir Samozanyatykh v8.2
Security Hardened: HttpOnly cookies, refresh rotation, CSRF, account enumeration protection
"""

import hashlib
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, validate_password,
    create_access_token, create_refresh_token,
    verify_access_token, verify_refresh_token, hash_token,
    generate_secure_token, generate_csrf_token,
    constant_time_compare, mask_email
)
from app.models import User, UserSession, AuditLog
from app.services.email import send_verification_email, send_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie settings
COOKIE_SETTINGS = {
    "httponly": True,
    "secure": True,
    "samesite": "strict",
    "path": "/api/auth/refresh",
    "max_age": 7 * 24 * 3600
}


def log_security_event(db: Session, user_id: int, action: str, ip: str, user_agent: str, success: bool = True, details: str = None):
    """Log security event without secrets"""
    safe_details = details or ""
    for secret_word in ["password", "token", "secret", "key", "jwt"]:
        safe_details = safe_details.replace(secret_word, "***")

    log = AuditLog(
        user_id=user_id,
        action=action,
        resource="auth",
        details=safe_details[:500],
        ip_address=ip,
        user_agent=user_agent[:200] if user_agent else None,
        success=success
    )
    db.add(log)
    db.commit()


@router.post("/register")
async def register(
    response: Response,
    email: str,
    password: str,
    full_name: str = None,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Register new user with strong password validation"""
    valid, msg = validate_password(password)
    if not valid:
        raise HTTPException(400, msg)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return {"message": "Registration initiated. Check your email."}

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_token = generate_secure_token()
    token_hash = hash_token(raw_token)
    user.email_verification_token_hash = token_hash
    user.email_verification_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.commit()

    await send_verification_email(email, raw_token)

    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="strict",
        max_age=3600
    )

    ip = request.client.host if request else None
    ua = request.headers.get("user-agent") if request else None
    log_security_event(db, user.id, "register", ip, ua, True, f"email={mask_email(email)}")

    return {
        "message": "Registration initiated. Check your email.",
        "csrf_token": csrf_token
    }


@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Login with HttpOnly refresh cookie + memory-only access token"""
    ip = request.client.host if request else None
    ua = request.headers.get("user-agent") if request else None

    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            db.commit()
            log_security_event(db, user.id, "login_failed", ip, ua, False, "invalid_password")
        raise HTTPException(401, "Invalid credentials")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        log_security_event(db, user.id, "login_locked", ip, ua, False)
        raise HTTPException(423, "Account temporarily locked. Try again later.")

    if not user.is_verified:
        raise HTTPException(403, "Email not verified. Please check your email.")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(user.id)
    refresh_token, jti = create_refresh_token(user.id)

    session = UserSession(
        user_id=user.id,
        jti=jti,
        token_type="refresh",
        token_hash=hash_token(refresh_token),
        ip_address=ip,
        user_agent=ua,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(session)
    db.commit()

    response.set_cookie(key="refresh_token", value=refresh_token, **COOKIE_SETTINGS)

    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="strict",
        max_age=3600
    )

    log_security_event(db, user.id, "login_success", ip, ua, True)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "csrf_token": csrf_token
    }


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token with rotation"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, "No refresh token provided")

    try:
        payload = verify_refresh_token(refresh_token)
    except HTTPException:
        raise HTTPException(401, "Invalid refresh token")

    jti = payload.get("jti")
    user_id = int(payload.get("sub"))

    token_hash = hash_token(refresh_token)
    session = db.query(UserSession).filter(
        UserSession.jti == jti,
        UserSession.token_hash == token_hash,
        UserSession.revoked == False,
        UserSession.expires_at > datetime.now(timezone.utc)
    ).first()

    if not session:
        db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.token_type == "refresh"
        ).update({"revoked": True})
        db.commit()
        raise HTTPException(401, "Token reuse detected. All sessions revoked.")

    session.revoked = True
    db.commit()

    new_access = create_access_token(user_id)
    new_refresh, new_jti = create_refresh_token(user_id)
    new_hash = hash_token(new_refresh)

    new_session = UserSession(
        user_id=user_id,
        jti=new_jti,
        token_type="refresh",
        token_hash=new_hash,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(new_session)
    db.commit()

    response.set_cookie(key="refresh_token", value=new_refresh, **COOKIE_SETTINGS)

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": 1800
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Logout — revoke refresh token, clear cookies"""
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        try:
            payload = verify_refresh_token(refresh_token)
            jti = payload.get("jti")
            user_id = int(payload.get("sub"))

            db.query(UserSession).filter(UserSession.jti == jti).update({"revoked": True})
            db.commit()

            ip = request.client.host
            ua = request.headers.get("user-agent")
            log_security_event(db, user_id, "logout", ip, ua, True)
        except:
            pass

    response.delete_cookie("refresh_token", path="/api/auth/refresh")
    response.delete_cookie("csrf_token")

    return {"message": "Logged out successfully"}


@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email with one-time token"""
    token_hash = hash_token(token)

    user = db.query(User).filter(
        User.email_verification_token_hash == token_hash,
        User.email_verification_expires_at > datetime.now(timezone.utc)
    ).first()

    if not user:
        raise HTTPException(400, "Invalid or expired verification link")

    user.is_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/password-reset-request")
async def request_password_reset(email: str, db: Session = Depends(get_db)):
    """Request password reset — same response for all cases"""
    user = db.query(User).filter(User.email == email).first()

    if user and user.is_verified:
        raw_token = generate_secure_token()
        token_hash = hash_token(raw_token)

        user.password_reset_token_hash = token_hash
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        user.password_reset_created_at = datetime.now(timezone.utc)
        db.commit()

        await send_reset_email(email, raw_token)

    return {"message": "If account exists, reset instructions sent"}


@router.post("/password-reset")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """Reset password with one-time token + revoke all sessions"""
    valid, msg = validate_password(new_password)
    if not valid:
        raise HTTPException(400, msg)

    token_hash = hash_token(token)

    user = db.query(User).filter(
        User.password_reset_token_hash == token_hash,
        User.password_reset_expires_at > datetime.now(timezone.utc)
    ).first()

    if not user:
        raise HTTPException(400, "Invalid or expired reset token")

    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    db.commit()

    user.password_hash = hash_password(new_password)

    db.query(UserSession).filter(UserSession.user_id == user.id).update({"revoked": True})
    db.commit()

    return {"message": "Password reset successfully. Please log in again."}
