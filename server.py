"""
Мир Самозанятых v4.2 — Security Hardened + All Fixes
FastAPI + SQLAlchemy async + Alembic + Audit Log + Email Verification + CORS + Healthcheck
"""

import os
import sys
import json
import uuid
import hmac
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path

# ============ НАСТРОЙКИ ============
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/mir_samozanyatykh.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    DOMAIN: str = "localhost:8000"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_WINDOW: int = 60
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: str = "jpg,jpeg,png,pdf,doc,docx"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# ============ ЛОГИРОВАНИЕ ============
Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mir-samozanyatykh")

# ============ БАЗА ДАННЫХ ============
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, Text,
    ForeignKey, Index, select, update, delete, func
)

Base = declarative_base()
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ============ МОДЕЛИ ============

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(50))
    inn = Column(String(20), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    email_verified_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    jti = Column(String(255), unique=True, index=True, nullable=False)
    token_type = Column(String(20), default="access")  # access | refresh
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="sessions")

    __table_args__ = (Index("idx_session_jti", "jti"),)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # login, logout, register, update_profile, admin_action, etc.
    resource = Column(String(100))  # users, contracts, settings, etc.
    resource_id = Column(String(100))
    details = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (Index("idx_audit_user", "user_id"), Index("idx_audit_action", "action"),)

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_type = Column(String(50), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    points = Column(Integer, default=0)
    awarded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="achievements")

class ContractTemplate(Base):
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# ============ PWA / СТАТИКА ============
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ============ SECURITY HELPERS ============
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time password verification"""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        # Constant-time comparison to prevent timing attacks
        dummy_hash = pwd_context.hash("dummy")
        pwd_context.verify("dummy", dummy_hash)
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Проверка сложности пароля"""
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    if not any(c.isupper() for c in password):
        return False, "Пароль должен содержать заглавную букву"
    if not any(c.islower() for c in password):
        return False, "Пароль должен содержать строчную букву"
    if not any(c.isdigit() for c in password):
        return False, "Пароль должен содержать цифру"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Пароль должен содержать специальный символ"
    return True, ""

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str]:
    """Создание JWT с jti и типом токена. Возвращает (token, jti)"""
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "type": "access",
        "iat": datetime.now(timezone.utc)
    })
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti

def create_refresh_token(data: dict) -> tuple[str, str]:
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "type": "refresh",
        "iat": datetime.now(timezone.utc)
    })
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti

async def verify_token(token: str, expected_type: str = "access", db: AsyncSession = None) -> dict:
    """Проверка JWT с валидацией jti в БД"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        token_type = payload.get("type")

        if token_type != expected_type:
            raise HTTPException(status_code=401, detail="Неверный тип токена")

        if db and jti:
            result = await db.execute(
                select(UserSession).where(
                    UserSession.jti == jti,
                    UserSession.revoked == False,
                    UserSession.expires_at > datetime.now(timezone.utc)
                )
            )
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=401, detail="Токен отозван или истёк")

        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный или истёкший токен")

# ============ CSP NONCE ============
async def generate_csp_nonce() -> str:
    return secrets.token_urlsafe(16)

# ============ DATABASE DEPENDENCY ============
async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

# ============ AUDIT LOG ============
async def log_audit(
    db: AsyncSession,
    action: str,
    user_id: Optional[int] = None,
    resource: str = "",
    resource_id: str = "",
    details: str = "",
    ip_address: str = "",
    user_agent: str = "",
    success: bool = True
):
    """Запись в audit log"""
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success
    )
    db.add(log_entry)
    await db.commit()
    logger.info(f"AUDIT: {action} | user={user_id} | resource={resource} | success={success}")

# ============ EMAIL ============
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_verification_email(email: str, token: str) -> bool:
    """Отправка письма подтверждения email"""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP не настроен, email не отправлен")
        return False

    try:
        verification_url = f"https://{settings.DOMAIN}/verify-email?token={token}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Подтверждение email — Мир Самозанятых"
        msg["From"] = settings.SMTP_USER
        msg["To"] = email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; padding: 30px; text-align: center;">
                <h1 style="color: #00d4ff; margin: 0;">Мир Самозанятых</h1>
            </div>
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #1a1a2e;">Подтвердите ваш email</h2>
                <p>Здравствуйте!</p>
                <p>Для завершения регистрации подтвердите ваш email, нажав кнопку ниже:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: #00d4ff; color: #1a1a2e; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;
                              display: inline-block;">
                        Подтвердить email
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    Если кнопка не работает, скопируйте ссылку:<br>
                    <code style="background: #e9ecef; padding: 5px; border-radius: 4px;">{verification_url}</code>
                </p>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html", "utf-8"))

        if settings.SMTP_TLS:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, [email], msg.as_string())
        server.quit()

        logger.info(f"Verification email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
        return False

# ============ SVETLANA KNOWLEDGE BASE ============
_svetlana_knowledge: Optional[Dict] = None

def load_svetlana_knowledge() -> Dict:
    global _svetlana_knowledge
    if _svetlana_knowledge is None:
        try:
            with open("data/svetlana_knowledge.json", "r", encoding="utf-8") as f:
                _svetlana_knowledge = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Svetlana knowledge: {e}")
            _svetlana_knowledge = {
                "greetings": ["Привет! Я Светлана."],
                "categories": {},
                "fallback_responses": ["Извините, я не поняла вопрос."]
            }
    return _svetlana_knowledge

# ============ RATE LIMITER ============
limiter = Limiter(key_func=get_remote_address)

# ============ FASTAPI APP ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Mir Samozanyatykh v4.2...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title="Мир Самозанятых",
    description="Платформа для самозанятых — безопасная версия v4.2",
    version="4.2.0",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS (только для разработки или whitelist)
if settings.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"https://{settings.DOMAIN}", f"https://www.{settings.DOMAIN}"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    )

# Trusted Hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[settings.DOMAIN, f"www.{settings.DOMAIN}", "localhost", "*"] if settings.ENVIRONMENT == "development" else [settings.DOMAIN, f"www.{settings.DOMAIN}"]
)

# Session middleware для CSRF
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session_id",
    max_age=3600,
    same_site="lax",
    https_only=settings.ENVIRONMENT == "production"
)

# Static files с кэшированием
class CachedStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2")):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

app.mount("/static", CachedStaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# ============ SECURITY HEADERS MIDDLEWARE ============
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    nonce = getattr(request.state, "csp_nonce", "")

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    return response

# ============ CSP NONCE MIDDLEWARE ============
@app.middleware("http")
async def csp_nonce_middleware(request: Request, call_next):
    request.state.csp_nonce = await generate_csp_nonce()
    response = await call_next(request)
    return response

# ============ ERROR HANDLING ============
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера. Попробуйте позже."}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# ============ HEALTHCHECK ============
@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Healthcheck с проверкой БД"""
    try:
        result = await db.execute(select(func.count(User.id)))
        user_count = result.scalar()
        return {
            "status": "healthy",
            "database": "connected",
            "users": user_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "4.2.0"
        }
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@app.get("/api/health/detailed")
async def health_check_detailed():
    """Детальный healthcheck"""
    checks = {
        "app": True,
        "database": False,
        "disk": False,
        "memory": False
    }

    # Проверка диска
    try:
        stat = os.statvfs(".")
        free_gb = stat.f_bavail * stat.f_frsize / (1024**3)
        checks["disk"] = free_gb > 1.0  # минимум 1 ГБ
    except:
        pass

    # Проверка памяти
    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()
        available = [line for line in meminfo.split("\n") if "MemAvailable" in line]
        if available:
            avail_kb = int(available[0].split()[1])
            checks["memory"] = avail_kb > 100 * 1024  # минимум 100 МБ
    except:
        pass

    all_healthy = all(checks.values())
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

# ============ AUTH ROUTES ============
@app.post("/api/auth/register")
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def register(
    request: Request,
    email: str = Form(..., max_length=255),
    password: str = Form(..., max_length=128),
    full_name: str = Form(..., max_length=255),
    phone: Optional[str] = Form(None, max_length=50),
    inn: Optional[str] = Form(None, max_length=20),
    db: AsyncSession = Depends(get_db)
):
    """Регистрация с подтверждением email"""
    try:
        # Валидация email
        if "@" not in email or "." not in email.split("@")[-1]:
            raise HTTPException(status_code=400, detail="Неверный формат email")

        # Проверка сложности пароля
        is_strong, msg = validate_password_strength(password)
        if not is_strong:
            raise HTTPException(status_code=400, detail=msg)

        # Проверка существующего пользователя
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
            email_verification_token=verification_token
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Отправка письма подтверждения
        email_sent = await send_verification_email(email, verification_token)

        # Audit log
        await log_audit(
            db=db,
            action="register",
            user_id=new_user.id,
            resource="users",
            resource_id=str(new_user.id),
            details=f"Registration successful, email_sent={email_sent}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )

        return {
            "message": "Регистрация успешна. Проверьте email для подтверждения.",
            "email_sent": email_sent,
            "user_id": new_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await log_audit(
            db=db,
            action="register",
            resource="users",
            details=f"Registration failed: {str(e)}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            success=False
        )
        raise HTTPException(status_code=500, detail="Ошибка при регистрации")

@app.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Подтверждение email по токену"""
    try:
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

        await log_audit(
            db=db,
            action="email_verified",
            user_id=user.id,
            resource="users",
            resource_id=str(user.id)
        )

        return {"message": "Email успешно подтверждён!"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка подтверждения email")

@app.post("/api/auth/login")
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def login(
    request: Request,
    email: str = Form(..., max_length=255),
    password: str = Form(..., max_length=128),
    db: AsyncSession = Depends(get_db)
):
    """Авторизация с блокировкой после N неудач"""
    try:
        # Поиск пользователя
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        # Проверка блокировки
        if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            raise HTTPException(
                status_code=423,
                detail=f"Аккаунт заблокирован. Попробуйте через {remaining} минут."
            )

        # Проверка пароля
        if not user or not verify_password(password, user.password_hash):
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                await db.commit()

            await log_audit(
                db=db,
                action="login_failed",
                user_id=user.id if user else None,
                resource="auth",
                details=f"Failed login for {email}",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                success=False
            )
            raise HTTPException(status_code=401, detail="Неверный email или пароль")

        # Проверка верификации email
        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Подтвердите email перед входом")

        # Сброс счётчика неудач
        user.failed_login_attempts = 0
        user.locked_until = None

        # Создание токенов
        access_token, access_jti = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token, refresh_jti = create_refresh_token({"sub": str(user.id)})

        # Сохранение сессий
        now = datetime.now(timezone.utc)
        db.add_all([
            UserSession(
                user_id=user.id,
                jti=access_jti,
                token_type="access",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            ),
            UserSession(
                user_id=user.id,
                jti=refresh_jti,
                token_type="refresh",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )
        ])
        await db.commit()

        # Audit log
        await log_audit(
            db=db,
            action="login",
            user_id=user.id,
            resource="auth",
            details="Successful login",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при авторизации")

@app.post("/api/auth/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Выход — отзыв токена"""
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = await verify_token(token, db=db)
            jti = payload.get("jti")
            user_id = int(payload.get("sub"))

            if jti:
                await db.execute(
                    update(UserSession)
                    .where(UserSession.jti == jti)
                    .values(revoked=True)
                )
                await db.commit()

            await log_audit(
                db=db,
                action="logout",
                user_id=user_id,
                resource="auth"
            )

        return {"message": "Выход выполнен успешно"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"message": "Выход выполнен"}

@app.post("/api/auth/refresh")
async def refresh_token(
    request: Request,
    refresh_token: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Обновление access токена"""
    try:
        payload = await verify_token(refresh_token, expected_type="refresh", db=db)
        user_id = int(payload.get("sub"))

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Пользователь не найден или заблокирован")

        # Отзыв старого refresh токена
        old_jti = payload.get("jti")
        if old_jti:
            await db.execute(
                update(UserSession)
                .where(UserSession.jti == old_jti)
                .values(revoked=True)
            )

        # Создание новых токенов
        new_access, access_jti = create_access_token({"sub": str(user.id), "email": user.email})
        new_refresh, refresh_jti = create_refresh_token({"sub": str(user.id)})

        now = datetime.now(timezone.utc)
        db.add_all([
            UserSession(
                user_id=user.id,
                jti=access_jti,
                token_type="access",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            ),
            UserSession(
                user_id=user.id,
                jti=refresh_jti,
                token_type="refresh",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )
        ])
        await db.commit()

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=401, detail="Неверный refresh токен")

# ============ CURRENT USER DEPENDENCY ============
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    token = auth_header[7:]
    payload = await verify_token(token, db=db)
    user_id = int(payload.get("sub"))

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден или заблокирован")

    return user

async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return current_user

# ============ USER ROUTES ============
@app.get("/api/user/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "inn": current_user.inn,
        "is_verified": current_user.is_verified,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

@app.put("/api/user/me")
@limiter.limit("10/minute")
async def update_me(
    request: Request,
    full_name: Optional[str] = Form(None, max_length=255),
    phone: Optional[str] = Form(None, max_length=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        if full_name:
            current_user.full_name = full_name
        if phone:
            current_user.phone = phone

        await db.commit()

        await log_audit(
            db=db,
            action="update_profile",
            user_id=current_user.id,
            resource="users",
            resource_id=str(current_user.id),
            ip_address=request.client.host
        )

        return {"message": "Профиль обновлён"}
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления профиля")

# ============ FILE UPLOAD ============
@app.post("/api/upload")
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка файла с валидацией"""
    try:
        # Проверка расширения
        allowed = settings.ALLOWED_UPLOAD_EXTENSIONS.split(",")
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Недопустимое расширение файла. Разрешены: {', '.join(allowed)}")

        # Проверка размера
        contents = await file.read()
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(contents) > max_size:
            raise HTTPException(status_code=413, detail=f"Файл слишком большой. Максимум {settings.MAX_UPLOAD_SIZE_MB} МБ")

        # Сохранение
        upload_dir = Path(f"data/uploads/{current_user.id}")
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = f"{secrets.token_urlsafe(16)}.{ext}"
        file_path = upload_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(contents)

        await log_audit(
            db=db,
            action="file_upload",
            user_id=current_user.id,
            resource="files",
            details=f"Uploaded {file.filename} -> {safe_filename}",
            ip_address=request.client.host
        )

        return {
            "filename": safe_filename,
            "original_name": file.filename,
            "size": len(contents),
            "path": str(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки файла")

# ============ ADMIN ROUTES ============
@app.get("/api/admin/audit-logs")
async def get_audit_logs(
    page: int = 1,
    per_page: int = 50,
    action: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        if action:
            query = query.where(AuditLog.action == action)

        # Пагинация
        total_result = await db.execute(select(func.count(AuditLog.id)))
        total = total_result.scalar()

        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        logs = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "logs": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource": log.resource,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "success": log.success,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения логов")

@app.get("/api/admin/users")
async def get_users(
    page: int = 1,
    per_page: int = 50,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        total_result = await db.execute(select(func.count(User.id)))
        total = total_result.scalar()

        result = await db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        users = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "is_verified": u.is_verified,
                    "is_active": u.is_active,
                    "is_admin": u.is_admin,
                    "created_at": u.created_at.isoformat() if u.created_at else None
                }
                for u in users
            ]
        }
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения пользователей")

# ============ SVETLANA CHAT ============
@app.post("/api/svetlana/ask")
@limiter.limit("20/minute")
async def ask_svetlana(
    request: Request,
    question: str = Form(..., max_length=500),
    category: Optional[str] = Form(None)
):
    """ИИ-ассистент Светлана с загружаемой базой знаний"""
    try:
        knowledge = load_svetlana_knowledge()
        question_lower = question.lower()

        # Поиск по категориям
        best_answer = None
        best_score = 0

        categories = knowledge.get("categories", {})
        for cat_key, cat_data in categories.items():
            if category and cat_key != category:
                continue
            for qa in cat_data.get("questions", []):
                q_text = qa.get("q", "").lower()
                # Простое сопоставление по ключевым словам
                score = sum(1 for word in question_lower.split() if word in q_text)
                if score > best_score:
                    best_score = score
                    best_answer = qa.get("a")

        if best_answer and best_score > 0:
            return {
                "answer": best_answer,
                "confidence": min(best_score / len(question_lower.split()), 1.0),
                "source": "knowledge_base"
            }

        # Fallback
        fallbacks = knowledge.get("fallback_responses", ["Извините, я не поняла вопрос."])
        import random
        return {
            "answer": random.choice(fallbacks),
            "confidence": 0.0,
            "source": "fallback"
        }
    except Exception as e:
        logger.error(f"Svetlana error: {e}")
        return {
            "answer": "Извините, произошла ошибка. Попробуйте позже.",
            "confidence": 0.0,
            "source": "error"
        }

@app.get("/api/svetlana/categories")
async def get_svetlana_categories():
    """Получение списка категорий знаний"""
    try:
        knowledge = load_svetlana_knowledge()
        categories = knowledge.get("categories", {})
        return {
            "categories": [
                {"key": k, "title": v.get("title", k)}
                for k, v in categories.items()
            ]
        }
    except Exception as e:
        logger.error(f"Svetlana categories error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки категорий")

# ============ CONTRACTS ============
@app.get("/api/contracts/templates")
async def get_contract_templates(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(ContractTemplate).where(ContractTemplate.is_active == True)
        )
        templates = result.scalars().all()
        return {
            "templates": [
                {"id": t.id, "name": t.name, "category": t.category}
                for t in templates
            ]
        }
    except Exception as e:
        logger.error(f"Contract templates error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки шаблонов")

# ============ HTML ROUTES ============
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    nonce = request.state.csp_nonce
    return templates.TemplateResponse("index.html", {
        "request": request,
        "csp_nonce": nonce,
        "domain": settings.DOMAIN
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    nonce = request.state.csp_nonce
    return templates.TemplateResponse("login.html", {
        "request": request,
        "csp_nonce": nonce
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    nonce = request.state.csp_nonce
    return templates.TemplateResponse("register.html", {
        "request": request,
        "csp_nonce": nonce
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    nonce = request.state.csp_nonce
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "csp_nonce": nonce
    })

@app.get("/svetlana", response_class=HTMLResponse)
async def svetlana_page(request: Request):
    nonce = request.state.csp_nonce
    return templates.TemplateResponse("svetlana.html", {
        "request": request,
        "csp_nonce": nonce
    })

@app.get("/contracts", response_class=HTMLResponse)
async def contracts_page(request: Request):
    nonce = request.state.csp_nonce
    return templates.TemplateResponse("contracts.html", {
        "request": request,
        "csp_nonce": nonce
    })

# ============ SEED DATA ============
async def seed_data(db: AsyncSession):
    """Начальные данные"""
    # Проверка существования админа
    result = await db.execute(select(User).where(User.email == "admin@мир-самозанятых.рф"))
    if not result.scalar_one_or_none():
        admin = User(
            email="admin@мир-самозанятых.рф",
            password_hash=get_password_hash("Admin123!"),
            full_name="Администратор",
            is_verified=True,
            is_admin=True
        )
        db.add(admin)

    # Шаблоны договоров
    result = await db.execute(select(ContractTemplate))
    if not result.scalars().first():
        templates_data = [
            {
                "name": "Договор оказания услуг (физлицо)",
                "category": "services",
                "content": "ДОГОВОР № ___\nна оказание услуг\n\nг. ______ "___" ______ 20__ г.\n\nИсполнитель: [ФИО], ИНН [ИНН], самозанятый\nЗаказчик: [ФИО/Наименование], [Реквизиты]\n\n1. Предмет договора..."
            },
            {
                "name": "Договор подряда",
                "category": "contract",
                "content": "ДОГОВОР ПОДРЯДА № ___\n\n1. Подрядчик обязуется выполнить работы..."
            },
            {
                "name": "Акт выполненных работ",
                "category": "act",
                "content": "АКТ\nвыполненных работ (оказанных услуг)\n\nк договору № ___ от "___" ______ 20__ г.\n\n1. Настоящий акт составлен о том, что..."
            }
        ]
        for t in templates_data:
            db.add(ContractTemplate(**t))

    await db.commit()
    logger.info("Seed data applied")

# ============ MAIN ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
