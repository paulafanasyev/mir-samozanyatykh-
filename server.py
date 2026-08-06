"""
Мир Самозанятых v5.0 — PostgreSQL Edition
FastAPI + SQLAlchemy async + PostgreSQL + AI + CRM + Finance + Marketplace + Gamification + Legal + Sales
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

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = ""
    ENVIRONMENT: str = "production"
    DATABASE_URL: str = "postgresql+asyncpg://mir_user:change_me_in_production@localhost:5432/mir_samozanyatykh"
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
    OPENROUTER_API_KEY: str = ""
    FNS_API_URL: str = "https://api-fns.ru/api/"
    FNS_API_KEY: str = ""
    CRYPTOPRO_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    SMS_RU_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Validate SECRET_KEY in production
if settings.ENVIRONMENT == "production" and len(settings.SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 chars in production. Generate: openssl rand -hex 64")


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

def get_celery_tasks():
    from tasks import send_email_task, send_sms_task, create_notification_task
    return send_email_task, send_sms_task, create_notification_task

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, Text,
    ForeignKey, Index, select, update, delete, func, JSON
)

Base = declarative_base()
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True, pool_recycle=300)
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
    subscription_tier = Column(String(20), default="free")
    subscription_expires = Column(DateTime)
    email_verification_token = Column(String(255))
    email_verified_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    telegram_id = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    clients = relationship("Client", back_populates="user")
    marketplace_profile = relationship("MarketplaceProfile", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    jti = Column(String(255), unique=True, index=True, nullable=False)
    token_type = Column(String(20), default="access")
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
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
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
    badge_icon = Column(String(50), default="🏆")
    awarded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="achievements")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(100))
    description = Column(Text)
    receipt_data = Column(JSON)
    fns_receipt_id = Column(String(100))
    transaction_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="transactions")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    company = Column(String(255))
    notes = Column(Text)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="clients")
    deals = relationship("Deal", back_populates="client")

class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    amount = Column(Float)
    status = Column(String(50), default="new")
    description = Column(Text)
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    client = relationship("Client", back_populates="deals")

class ContractTemplate(Base):
    __tablename__ = "contract_templates"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    content = Column(Text, nullable=False)
    variables = Column(JSON)
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SignedContract(Base):
    __tablename__ = "signed_contracts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey("contract_templates.id"))
    title = Column(String(255))
    content = Column(Text)
    variables_data = Column(JSON)
    signature_hash = Column(String(255))
    signed_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MarketplaceProfile(Base):
    __tablename__ = "marketplace_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    slug = Column(String(100), unique=True, index=True)
    bio = Column(Text)
    services = Column(JSON)
    portfolio = Column(JSON)
    hourly_rate = Column(Float)
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="marketplace_profile")
    reviews = relationship("Review", back_populates="profile")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("marketplace_profiles.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String(255))
    author_email = Column(String(255))
    rating = Column(Integer, nullable=False)
    text = Column(Text)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    profile = relationship("MarketplaceProfile", back_populates="reviews")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    message = Column(Text)
    type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="notifications")

class GrantApplication(Base):
    __tablename__ = "grant_applications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    grant_type = Column(String(100), nullable=False)
    status = Column(String(50), default="draft")
    data = Column(JSON)
    ai_score = Column(Float)
    submitted_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SMSLog(Base):
    __tablename__ = "sms_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    phone = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, delivered, failed
    sms_ru_id = Column(String(100))
    cost = Column(Float)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User")

# ============ FASTAPI SETUP ============
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, UploadFile, File, Form, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        dummy_hash = pwd_context.hash("dummy")
        pwd_context.verify("dummy", dummy_hash)
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> tuple[bool, str]:
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
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "jti": jti, "type": "access", "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM), jti

def create_refresh_token(data: dict) -> tuple[str, str]:
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh", "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM), jti

async def verify_token(token: str, expected_type: str = "access", db: AsyncSession = None) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(status_code=401, detail="Неверный тип токена")
        if db and jti:
            result = await db.execute(
                select(UserSession).where(UserSession.jti == jti, UserSession.revoked == False,
                                          UserSession.expires_at > datetime.now(timezone.utc)))
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=401, detail="Токен отозван или истёк")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный или истёкший токен")

async def generate_csp_nonce() -> str:
    return secrets.token_urlsafe(16)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def log_audit(db: AsyncSession, action: str, user_id: Optional[int] = None,
                    resource: str = "", resource_id: str = "", details: str = "",
                    ip_address: str = "", user_agent: str = "", success: bool = True):
    db.add(AuditLog(user_id=user_id, action=action, resource=resource, resource_id=resource_id,
                    details=details, ip_address=ip_address, user_agent=user_agent, success=success))
    await db.commit()
    logger.info(f"AUDIT: {action} | user={user_id} | resource={resource} | success={success}")

# ============ EMAIL ============
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_verification_email(email: str, token: str) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP не настроен")
        return False
    try:
        verification_url = f"https://{settings.DOMAIN}/verify-email?token={token}"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Подтверждение email — Мир Самозанятых"
        msg["From"] = settings.SMTP_USER
        msg["To"] = email
        html = f"""<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#1a1a2e;padding:30px;text-align:center;"><h1 style="color:#00d4ff;margin:0;">Мир Самозанятых</h1></div>
        <div style="padding:30px;background:#f8f9fa;"><h2 style="color:#1a1a2e;">Подтвердите ваш email</h2>
        <p>Для завершения регистрации нажмите кнопку:</p>
        <div style="text-align:center;margin:30px 0;"><a href="{verification_url}" style="background:#00d4ff;color:#1a1a2e;padding:15px 40px;text-decoration:none;border-radius:8px;font-weight:bold;display:inline-block;">Подтвердить email</a></div>
        <p style="color:#666;font-size:14px;">Если кнопка не работает:<br><code style="background:#e9ecef;padding:5px;border-radius:4px;">{verification_url}</code></p></div></body></html>"""
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
        logger.error(f"Failed to send email: {e}")
        return False

# ============ AI / OPENROUTER ============
import httpx

async def ask_ai(question: str, context: str = "", model: str = "anthropic/claude-3.5-sonnet") -> str:
    if not settings.OPENROUTER_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                         "HTTP-Referer": f"https://{settings.DOMAIN}", "X-Title": "Мир Самозанятых"},
                json={"model": model, "messages": [
                    {"role": "system", "content": f"Ты Светлана, ИИ-ассистент для самозанятых в России. {context}"},
                    {"role": "user", "content": question}
                ], "temperature": 0.7, "max_tokens": 1000})
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"AI error: {e}")
        return None

# ============ FNS API ============
async def check_inn_fns(inn: str) -> dict:
    if not settings.FNS_API_KEY:
        return {"status": "no_api_key"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.FNS_API_URL}check", params={"inn": inn, "key": settings.FNS_API_KEY})
            return response.json()
    except Exception as e:
        logger.error(f"FNS API error: {e}")
        return {"status": "error", "message": str(e)}

# ============ SVETLANA KNOWLEDGE ============
_svetlana_knowledge: Optional[Dict] = None

def load_svetlana_knowledge() -> Dict:
    global _svetlana_knowledge
    if _svetlana_knowledge is None:
        try:
            with open("data/svetlana_knowledge.json", "r", encoding="utf-8") as f:
                _svetlana_knowledge = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load knowledge: {e}")
            _svetlana_knowledge = {"greetings": ["Привет!"], "categories": {}, "fallback_responses": ["Извините..."]}
    return _svetlana_knowledge

# ============ GAMIFICATION ============
ACHIEVEMENTS = {
    "first_login": {"title": "Первые шаги", "description": "Выполнен первый вход", "points": 10, "icon": "👣"},
    "profile_complete": {"title": "Открытая книга", "description": "Профиль заполнен на 100%", "points": 25, "icon": "📖"},
    "first_transaction": {"title": "Первый доход", "description": "Добавлена первая транзакция", "points": 20, "icon": "💰"},
    "first_client": {"title": "Нетворкинг", "description": "Добавлен первый клиент", "points": 15, "icon": "🤝"},
    "first_contract": {"title": "Юрист", "description": "Подписан первый договор", "points": 30, "icon": "📄"},
    "marketplace_created": {"title": "На рынке", "description": "Создан профиль в маркетплейсе", "points": 20, "icon": "🏪"},
    "first_review": {"title": "Рекомендация", "description": "Получен первый отзыв", "points": 25, "icon": "⭐"},
    "streak_7": {"title": "Неделя продуктивности", "description": "7 дней подряд в системе", "points": 50, "icon": "🔥"},
    "grant_applied": {"title": "Амбициозный", "description": "Подана заявка на грант", "points": 40, "icon": "🚀"},
    "tax_paid": {"title": "Честный налогоплательщик", "description": "Зафиксирована уплата налога", "points": 35, "icon": "🏛️"},
}

async def award_achievement(db: AsyncSession, user_id: int, achievement_type: str):
    if achievement_type not in ACHIEVEMENTS:
        return None
    result = await db.execute(select(UserAchievement).where(
        UserAchievement.user_id == user_id, UserAchievement.achievement_type == achievement_type))
    if result.scalar_one_or_none():
        return None
    ach = ACHIEVEMENTS[achievement_type]
    db.add(UserAchievement(user_id=user_id, achievement_type=achievement_type, title=ach["title"],
                           description=ach["description"], points=ach["points"], badge_icon=ach["icon"]))
    await db.commit()
    db.add(Notification(user_id=user_id, title=f"🏆 Новое достижение: {ach['title']}",
                        message=f"{ach['description']}. +{ach['points']} баллов!", type="success"))
    await db.commit()
    return True

async def get_user_points(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(func.sum(UserAchievement.points)).where(UserAchievement.user_id == user_id))
    return result.scalar() or 0

# ============ SUBSCRIPTION ============
async def check_subscription(user: User, required_tier: str) -> bool:
    tiers = {"free": 0, "pro": 1, "business": 2, "enterprise": 3}
    user_tier = tiers.get(user.subscription_tier, 0)
    required = tiers.get(required_tier, 0)
    if user_tier < required:
        return False
    if user.subscription_expires and user.subscription_expires < datetime.now(timezone.utc):
        return False
    return True

# ============ RATE LIMITER & APP ============
limiter = Limiter(key_func=get_remote_address)


# ============ WEBSOCKET CONNECTION MANAGER ============
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.global_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: int = None):
        await websocket.accept()
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
        self.global_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int = None):
        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def notify_user(self, user_id: int, title: str, message: str, notification_type: str = "info"):
        await self.send_personal_message({
            "type": "notification",
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, user_id)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Mir Samozanyatykh v5.0 (PostgreSQL)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title="Мир Самозанятых",
    description="Платформа для самозанятых — SMS Edition v5.2",
    version="5.2.0",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if settings.ENVIRONMENT == "development":
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:8000"],
                       allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])
else:
    app.add_middleware(CORSMiddleware, allow_origins=[f"https://{settings.DOMAIN}", f"https://www.{settings.DOMAIN}"],
                       allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE"],
                       allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"])

app.add_middleware(TrustedHostMiddleware,
    allowed_hosts=[settings.DOMAIN, f"www.{settings.DOMAIN}", "localhost", "*"] if settings.ENVIRONMENT == "development" else [settings.DOMAIN, f"www.{settings.DOMAIN}"])

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, session_cookie="session_id",
                   max_age=3600, same_site="lax", https_only=settings.ENVIRONMENT == "production")

class CachedStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2")):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

app.mount("/static", CachedStaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    nonce = getattr(request.state, "csp_nonce", "")
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self' 'unsafe-inline'; "
        f"font-src 'self'; "
        f"img-src 'self' data:; "
        f"connect-src 'self'; "
        f"frame-ancestors 'none'; "
        f"base-uri 'none'; "
        f"form-action 'self'"
    )
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response

@app.middleware("http")
async def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)

async def csp_nonce_middleware(request: Request, call_next):
    request.state.csp_nonce = await generate_csp_nonce()
    request.state.csrf_token = await generate_csrf_token()
    response = await call_next(request)
    # Set CSRF cookie for forms
    if request.method == "GET" and not request.cookies.get("csrf_token"):
        response.set_cookie("csrf_token", request.state.csrf_token, httponly=False, samesite="strict", secure=settings.ENVIRONMENT == "production")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера. Попробуйте позже."})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# ============ HEALTHCHECK ============
@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(func.count(User.id)))
        return {"status": "healthy", "database": "connected", "users": result.scalar(),
                "timestamp": datetime.now(timezone.utc).isoformat(), "version": "5.0.0"}
    except Exception as e:
        logger.error(f"Healthcheck failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "disconnected",
                "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()})

# ============ AUTH ============
@app.post("/api/auth/register")
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def register(request: Request, email: str = Form(..., max_length=255),
                   password: str = Form(..., max_length=128), full_name: str = Form(..., max_length=255),
                   phone: Optional[str] = Form(None, max_length=50), inn: Optional[str] = Form(None, max_length=20),
                   db: AsyncSession = Depends(get_db)):
    try:
        if "@" not in email or "." not in email.split("@")[-1]:
            raise HTTPException(status_code=400, detail="Неверный формат email")
        is_strong, msg = validate_password_strength(password)
        if not is_strong:
            raise HTTPException(status_code=400, detail=msg)
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
        verification_token = secrets.token_urlsafe(32)
        new_user = User(email=email, password_hash=get_password_hash(password), full_name=full_name,
                       phone=phone, inn=inn, is_verified=False, email_verification_token=verification_token)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        email_sent = await send_verification_email(email, verification_token)
        await log_audit(db=db, action="register", user_id=new_user.id, resource="users",
                       resource_id=str(new_user.id), details=f"Registration, email_sent={email_sent}",
                       ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""))
        return {"message": "Регистрация успешна. Проверьте email.", "email_sent": email_sent, "user_id": new_user.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при регистрации")

@app.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.email_verification_token == token))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=400, detail="Неверный или истёкший токен")
        user.is_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.email_verification_token = None
        await db.commit()
        await log_audit(db=db, action="email_verified", user_id=user.id, resource="users", resource_id=str(user.id))
        await award_achievement(db, user.id, "first_login")
        return {"message": "Email успешно подтверждён!"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка подтверждения email")

@app.post("/api/auth/login")
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def login(request: Request, email: str = Form(..., max_length=255),
                password: str = Form(..., max_length=128), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            raise HTTPException(status_code=423, detail=f"Аккаунт заблокирован. Попробуйте через {remaining} минут.")
        if not user or not verify_password(password, user.password_hash):
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                await db.commit()
            await log_audit(db=db, action="login_failed", user_id=user.id if user else None,
                           resource="auth", details=f"Failed login for {email}",
                           ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""), success=False)
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Подтвердите email перед входом")
        user.failed_login_attempts = 0
        user.locked_until = None
        access_token, access_jti = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token, refresh_jti = create_refresh_token({"sub": str(user.id)})
        now = datetime.now(timezone.utc)
        db.add_all([
            UserSession(user_id=user.id, jti=access_jti, token_type="access", ip_address=request.client.host,
                       user_agent=request.headers.get("user-agent", ""), expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
            UserSession(user_id=user.id, jti=refresh_jti, token_type="refresh", ip_address=request.client.host,
                       user_agent=request.headers.get("user-agent", ""), expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))])
        await db.commit()
        await log_audit(db=db, action="login", user_id=user.id, resource="auth", details="Successful login",
                       ip_address=request.client.host, user_agent=request.headers.get("user-agent", ""))
        await award_achievement(db, user.id, "first_login")
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "tier": user.subscription_tier}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при авторизации")

@app.post("/api/auth/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = await verify_token(token, db=db)
            jti = payload.get("jti")
            user_id = int(payload.get("sub"))
            if jti:
                await db.execute(update(UserSession).where(UserSession.jti == jti).values(revoked=True))
                await db.commit()
            await log_audit(db=db, action="logout", user_id=user_id, resource="auth")
        return {"message": "Выход выполнен успешно"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"message": "Выход выполнен"}

# ============ CURRENT USER ============
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
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

async def validate_csrf_token(request: Request):
    """Validate CSRF token for state-changing operations"""
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        header_token = request.headers.get("X-CSRF-Token")
        cookie_token = request.cookies.get("csrf_token")
        if not header_token or not cookie_token or header_token != cookie_token:
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
    return True

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return current_user

async def require_subscription(tier: str):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if not await check_subscription(current_user, tier):
            raise HTTPException(status_code=403, detail=f"Требуется подписка уровня {tier}")
        return current_user
    return checker

# ============ USER PROFILE ============
@app.get("/api/user/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    points = await get_user_points(db, current_user.id)
    return {"id": current_user.id, "email": current_user.email, "full_name": current_user.full_name,
            "phone": current_user.phone, "inn": current_user.inn, "is_verified": current_user.is_verified,
            "is_admin": current_user.is_admin, "tier": current_user.subscription_tier,
            "points": points, "created_at": current_user.created_at.isoformat() if current_user.created_at else None}

@app.put("/api/user/me")
@limiter.limit("10/minute")
async def update_me(request: Request, full_name: Optional[str] = Form(None, max_length=255),
                    phone: Optional[str] = Form(None, max_length=50),
                    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        if full_name:
            current_user.full_name = full_name
        if phone:
            current_user.phone = phone
        await db.commit()
        await log_audit(db=db, action="update_profile", user_id=current_user.id, resource="users",
                       resource_id=str(current_user.id), ip_address=request.client.host)
        if current_user.full_name and current_user.phone and current_user.inn:
            await award_achievement(db, current_user.id, "profile_complete")
        return {"message": "Профиль обновлён"}
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления профиля")

# ============ FINANCE / TRANSACTIONS ============
@app.post("/api/finance/transactions")
async def create_transaction(request: Request, amount: float = Form(...), category: str = Form(..., max_length=100),
                             description: Optional[str] = Form(None, max_length=500),
                             current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        transaction = Transaction(user_id=current_user.id, amount=amount, category=category,
                                  description=description, transaction_date=datetime.now(timezone.utc))
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        await award_achievement(db, current_user.id, "first_transaction")
        # TODO: Add optimistic locking (version column) for financial operations
        # to prevent race conditions in concurrent transactions
        await log_audit(db=db, action="transaction_created", user_id=current_user.id,
                       resource="transactions", resource_id=str(transaction.id))
        return {"id": transaction.id, "message": "Транзакция добавлена"}
    except Exception as e:
        logger.error(f"Transaction error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления транзакции")

@app.get("/api/finance/transactions")
async def get_transactions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                           page: int = 1, per_page: int = 50, category: Optional[str] = None,
                           date_from: Optional[str] = None, date_to: Optional[str] = None):
    try:
        query = select(Transaction).where(Transaction.user_id == current_user.id).order_by(Transaction.transaction_date.desc())
        if category:
            query = query.where(Transaction.category == category)
        if date_from:
            query = query.where(Transaction.transaction_date >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.where(Transaction.transaction_date <= datetime.fromisoformat(date_to))
        total_result = await db.execute(select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id))
        total = total_result.scalar()
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        transactions = result.scalars().all()
        income_result = await db.execute(select(func.sum(Transaction.amount)).where(
            Transaction.user_id == current_user.id, Transaction.amount > 0))
        expense_result = await db.execute(select(func.sum(Transaction.amount)).where(
            Transaction.user_id == current_user.id, Transaction.amount < 0))
        return {"total": total, "page": page, "per_page": per_page,
                "income": income_result.scalar() or 0, "expense": abs(expense_result.scalar() or 0),
                "transactions": [{"id": t.id, "amount": t.amount, "category": t.category,
                                  "description": t.description, "date": t.transaction_date.isoformat() if t.transaction_date else None}
                                 for t in transactions]}
    except Exception as e:
        logger.error(f"Get transactions error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения транзакций")

@app.get("/api/finance/stats")
async def finance_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(func.to_char(Transaction.transaction_date, "YYYY-MM").label("month"),
                                          func.sum(Transaction.amount).label("total"))
                                   .where(Transaction.user_id == current_user.id, Transaction.amount > 0)
                                   .group_by("month").order_by("month"))
        monthly = result.all()
        result = await db.execute(select(Transaction.category, func.sum(Transaction.amount).label("total"))
                                   .where(Transaction.user_id == current_user.id).group_by(Transaction.category))
        by_category = result.all()
        return {"monthly": [{"month": m.month, "total": m.total} for m in monthly],
                "by_category": [{"category": c.category, "total": c.total} for c in by_category],
                "tax_estimate": sum(m.total for m in monthly[-3:] if m.total) * 0.04 if monthly else 0}
    except Exception as e:
        logger.error(f"Finance stats error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка статистики")

# ============ CRM / CLIENTS ============
@app.post("/api/crm/clients")
async def create_client(request: Request, name: str = Form(..., max_length=255),
                        email: Optional[str] = Form(None, max_length=255),
                        phone: Optional[str] = Form(None, max_length=50),
                        company: Optional[str] = Form(None, max_length=255),
                        notes: Optional[str] = Form(None),
                        current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        client = Client(user_id=current_user.id, name=name, email=email, phone=phone, company=company, notes=notes)
        db.add(client)
        await db.commit()
        await db.refresh(client)
        await award_achievement(db, current_user.id, "first_client")
        await log_audit(db=db, action="client_created", user_id=current_user.id,
                       resource="clients", resource_id=str(client.id))
        return {"id": client.id, "message": "Клиент добавлен"}
    except Exception as e:
        logger.error(f"Client error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления клиента")

@app.get("/api/crm/clients")
async def get_clients(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Client).where(Client.user_id == current_user.id).order_by(Client.created_at.desc()))
        clients = result.scalars().all()
        return {"clients": [{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone,
                             "company": c.company, "status": c.status, "created_at": c.created_at.isoformat() if c.created_at else None}
                            for c in clients]}
    except Exception as e:
        logger.error(f"Get clients error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения клиентов")

@app.post("/api/crm/deals")
async def create_deal(request: Request, client_id: int = Form(...), title: str = Form(..., max_length=255),
                      amount: Optional[float] = Form(None), description: Optional[str] = Form(None),
                      deadline: Optional[str] = Form(None),
                      current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        deal = Deal(user_id=current_user.id, client_id=client_id, title=title, amount=amount,
                    description=description, deadline=datetime.fromisoformat(deadline) if deadline else None)
        db.add(deal)
        await db.commit()
        await db.refresh(deal)
        db.add(Notification(user_id=current_user.id, title="Новая сделка", message=f"Создана сделка: {title}", type="success"))
        await db.commit()
        return {"id": deal.id, "message": "Сделка создана"}
    except Exception as e:
        logger.error(f"Deal error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания сделки")

@app.get("/api/crm/deals")
async def get_deals(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Deal, Client).join(Client, Deal.client_id == Client.id)
                                   .where(Deal.user_id == current_user.id).order_by(Deal.created_at.desc()))
        deals = result.all()
        return {"deals": [{"id": d.id, "title": d.title, "client_name": c.name, "amount": d.amount,
                           "status": d.status, "deadline": d.deadline.isoformat() if d.deadline else None}
                          for d, c in deals]}
    except Exception as e:
        logger.error(f"Get deals error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения сделок")

# ============ CONTRACTS ============
@app.get("/api/contracts/templates")
async def get_contract_templates(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        query = select(ContractTemplate).where(ContractTemplate.is_active == True)
        result = await db.execute(query)
        templates = result.scalars().all()
        return {"templates": [{"id": t.id, "name": t.name, "category": t.category,
                               "is_premium": t.is_premium,
                               "locked": t.is_premium and not await check_subscription(current_user, "pro")}
                              for t in templates]}
    except Exception as e:
        logger.error(f"Contract templates error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки шаблонов")

@app.post("/api/contracts/generate")
async def generate_contract(request: Request, template_id: int = Form(...), variables: str = Form(...),
                            current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ContractTemplate).where(ContractTemplate.id == template_id))
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
        if template.is_premium and not await check_subscription(current_user, "pro"):
            raise HTTPException(status_code=403, detail="Требуется подписка Профи")
        vars_data = json.loads(variables)
        content = template.content
        for key, value in vars_data.items():
            content = content.replace(f"[{key}]", str(value))
        signed = SignedContract(user_id=current_user.id, template_id=template_id, title=template.name,
                                content=content, variables_data=vars_data)
        db.add(signed)
        await db.commit()
        await db.refresh(signed)
        await award_achievement(db, current_user.id, "first_contract")
        await log_audit(db=db, action="contract_generated", user_id=current_user.id,
                       resource="contracts", resource_id=str(signed.id))
        return {"id": signed.id, "content": content, "message": "Договор сгенерирован"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contract generation error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации договора")

# ============ MARKETPLACE ============
@app.post("/api/marketplace/profile")
async def create_marketplace_profile(request: Request, slug: str = Form(..., max_length=100),
                                     bio: Optional[str] = Form(None), services: Optional[str] = Form(None),
                                     hourly_rate: Optional[float] = Form(None),
                                     current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(MarketplaceProfile).where(MarketplaceProfile.slug == slug))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Этот URL уже занят")
        profile = MarketplaceProfile(user_id=current_user.id, slug=slug, bio=bio,
                                     services=json.loads(services) if services else [],
                                     hourly_rate=hourly_rate, is_visible=True)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        await award_achievement(db, current_user.id, "marketplace_created")
        return {"slug": profile.slug, "url": f"https://{settings.DOMAIN}/marketplace/{slug}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Marketplace profile error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания профиля")

@app.get("/api/marketplace/profiles")
async def search_marketplace(q: Optional[str] = None, category: Optional[str] = None,
                             page: int = 1, per_page: int = 20, db: AsyncSession = Depends(get_db)):
    try:
        query = select(MarketplaceProfile, User).join(User, MarketplaceProfile.user_id == User.id).where(MarketplaceProfile.is_visible == True)
        if q:
            query = query.where((MarketplaceProfile.bio.ilike(f"%{q}%")) | (User.full_name.ilike(f"%{q}%")))
        total_result = await db.execute(select(func.count(MarketplaceProfile.id)).where(MarketplaceProfile.is_visible == True))
        total = total_result.scalar()
        query = query.order_by(MarketplaceProfile.rating.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        profiles = result.all()
        return {"total": total, "page": page, "per_page": per_page,
                "profiles": [{"slug": p.slug, "name": u.full_name, "bio": p.bio, "services": p.services,
                              "hourly_rate": p.hourly_rate, "rating": p.rating, "reviews_count": p.reviews_count}
                             for p, u in profiles]}
    except Exception as e:
        logger.error(f"Marketplace search error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка поиска")

@app.post("/api/marketplace/reviews")
async def add_review(profile_slug: str = Form(...), author_name: str = Form(..., max_length=255),
                     rating: int = Form(...), text: Optional[str] = Form(None), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(MarketplaceProfile).where(MarketplaceProfile.slug == profile_slug))
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Профиль не найден")
        db.add(Review(profile_id=profile.id, author_name=author_name, rating=rating, text=text))
        result = await db.execute(select(func.avg(Review.rating)).where(Review.profile_id == profile.id))
        avg_rating = result.scalar() or 0
        profile.rating = round(avg_rating, 2)
        profile.reviews_count = await db.scalar(select(func.count(Review.id)).where(Review.profile_id == profile.id))
        await db.commit()
        await award_achievement(db, profile.user_id, "first_review")
        return {"message": "Отзыв добавлен"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления отзыва")

# ============ GRANTS ============
@app.post("/api/grants/apply")
async def apply_grant(request: Request, grant_type: str = Form(..., max_length=100), data: str = Form(...),
                      current_user: User = Depends(require_subscription("pro")), db: AsyncSession = Depends(get_db)):
    try:
        application = GrantApplication(user_id=current_user.id, grant_type=grant_type,
                                       data=json.loads(data), status="draft")
        db.add(application)
        await db.commit()
        await db.refresh(application)
        ai_feedback = None
        if settings.OPENROUTER_API_KEY:
            ai_feedback = await ask_ai(f"Оцени бизнес-план на грант типа {grant_type}. Данные: {data}",
                                       context="Ты эксперт по грантам для самозанятых в России.")
            if ai_feedback:
                application.ai_score = 7.5
                await db.commit()
        await award_achievement(db, current_user.id, "grant_applied")
        return {"id": application.id, "status": "draft", "ai_feedback": ai_feedback}
    except Exception as e:
        logger.error(f"Grant application error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка подготовки заявки")

@app.get("/api/grants/templates")
async def get_grant_templates():
    return {"grants": [
        {"type": "social_contract", "title": "Социальный контракт", "amount": "до 350 000 ₽", "description": "Для малоимущих и безработных"},
        {"type": "youth_grant", "title": "Грант молодым", "amount": "100 000–500 000 ₽", "description": "Для молодёжи до 35 лет"},
        {"type": "agro_startup", "title": "Агростартап", "amount": "до 3 000 000 ₽", "description": "Для сельскохозяйственных проектов"},
        {"type": "family_farm", "title": "Семейная ферма", "amount": "до 1 500 000 ₽", "description": "Для семейных сельхозпроизводителей"},
    ]}

# ============ NOTIFICATIONS ============
@app.get("/api/notifications")
async def get_notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                            unread_only: bool = False):
    try:
        query = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
        if unread_only:
            query = query.where(Notification.is_read == False)
        result = await db.execute(query.limit(50))
        notifications = result.scalars().all()
        unread_count = await db.scalar(select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id, Notification.is_read == False))
        return {"unread_count": unread_count,
                "notifications": [{"id": n.id, "title": n.title, "message": n.message,
                                   "type": n.type, "is_read": n.is_read, "created_at": n.created_at.isoformat()}
                                  for n in notifications]}
    except Exception as e:
        logger.error(f"Notifications error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения уведомлений")

@app.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user),
                                  db: AsyncSession = Depends(get_db)):
    await db.execute(update(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id).values(is_read=True))
    await db.commit()
    return {"message": "Отмечено как прочитанное"}

# ============ GAMIFICATION ============
@app.get("/api/gamification/achievements")
async def get_achievements(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(UserAchievement).where(UserAchievement.user_id == current_user.id)
                                   .order_by(UserAchievement.awarded_at.desc()))
        achievements = result.scalars().all()
        points = await get_user_points(db, current_user.id)
        user_ach_types = {a.achievement_type for a in achievements}
        all_achievements = []
        for ach_type, ach_data in ACHIEVEMENTS.items():
            all_achievements.append({"type": ach_type, "title": ach_data["title"],
                                     "description": ach_data["description"], "points": ach_data["points"],
                                     "icon": ach_data["icon"], "earned": ach_type in user_ach_types})
        return {"total_points": points, "earned_count": len(achievements), "total_count": len(ACHIEVEMENTS),
                "achievements": all_achievements,
                "earned": [{"type": a.achievement_type, "title": a.title, "points": a.points,
                            "icon": a.badge_icon, "awarded_at": a.awarded_at.isoformat()}
                           for a in achievements]}
    except Exception as e:
        logger.error(f"Achievements error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения достижений")

@app.get("/api/gamification/leaderboard")
async def get_leaderboard(db: AsyncSession = Depends(get_db), limit: int = 20):
    try:
        result = await db.execute(select(User.id, User.full_name, func.sum(UserAchievement.points).label("total_points"))
                                   .join(UserAchievement, User.id == UserAchievement.user_id)
                                   .group_by(User.id).order_by(func.sum(UserAchievement.points).desc()).limit(limit))
        leaders = result.all()
        return {"leaderboard": [{"rank": i + 1, "name": name or "Аноним", "points": int(points) if points else 0}
                                for i, (_, name, points) in enumerate(leaders)]}
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения лидерборда")

# ============ SVETLANA AI ============
@app.post("/api/svetlana/ask")
@limiter.limit("20/minute")
async def ask_svetlana(request: Request, question: str = Form(..., max_length=500),
                       category: Optional[str] = Form(None), use_ai: bool = Form(False),
                       current_user: Optional[User] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        if use_ai and settings.OPENROUTER_API_KEY:
            context = ""
            if current_user:
                context = f"Пользователь: {current_user.full_name}, ИНН: {current_user.inn or 'не указан'}"
            ai_answer = await ask_ai(question, context=context)
            if ai_answer:
                return {"answer": ai_answer, "confidence": 0.95, "source": "ai_openrouter"}
        knowledge = load_svetlana_knowledge()
        question_lower = question.lower()
        best_answer = None
        best_score = 0
        categories = knowledge.get("categories", {})
        for cat_key, cat_data in categories.items():
            if category and cat_key != category:
                continue
            for qa in cat_data.get("questions", []):
                q_text = qa.get("q", "").lower()
                score = sum(1 for word in question_lower.split() if word in q_text)
                if score > best_score:
                    best_score = score
                    best_answer = qa.get("a")
        if best_answer and best_score > 0:
            return {"answer": best_answer, "confidence": min(best_score / len(question_lower.split()), 1.0), "source": "knowledge_base"}
        fallbacks = knowledge.get("fallback_responses", ["Извините, я не поняла вопрос."])
        import random
        return {"answer": random.choice(fallbacks), "confidence": 0.0, "source": "fallback"}
    except Exception as e:
        logger.error(f"Svetlana error: {e}")
        return {"answer": "Извините, произошла ошибка. Попробуйте позже.", "confidence": 0.0, "source": "error"}

@app.get("/api/svetlana/categories")
async def get_svetlana_categories():
    try:
        knowledge = load_svetlana_knowledge()
        categories = knowledge.get("categories", {})
        return {"categories": [{"key": k, "title": v.get("title", k)} for k, v in categories.items()]}
    except Exception as e:
        logger.error(f"Svetlana categories error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки категорий")

# ============ FNS INTEGRATION ============
@app.get("/api/fns/check-inn")
@limiter.limit("10/minute")
async def check_inn(request: Request, inn: str = Query(..., min_length=10, max_length=12), current_user: User = Depends(get_current_user)):
    return await check_inn_fns(inn)

# ============ FILE UPLOAD ============
@app.post("/api/upload")
@limiter.limit("10/minute")
async def upload_file(request: Request, file: UploadFile = File(...),
                      current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        allowed = settings.ALLOWED_UPLOAD_EXTENSIONS.split(",")
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Недопустимое расширение. Разрешены: {', '.join(allowed)}")
        contents = await file.read()
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(contents) > max_size:
            raise HTTPException(status_code=413, detail=f"Файл слишком большой. Максимум {settings.MAX_UPLOAD_SIZE_MB} МБ")
        upload_dir = Path(f"data/uploads/{current_user.id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{secrets.token_urlsafe(16)}.{ext}"
        file_path = upload_dir / safe_filename
        with open(file_path, "wb") as f:
            f.write(contents)
        await log_audit(db=db, action="file_upload", user_id=current_user.id, resource="files",
                       details=f"Uploaded {file.filename} -> {safe_filename}", ip_address=request.client.host)
        return {"filename": safe_filename, "original_name": file.filename, "size": len(contents), "path": str(file_path)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки файла")

# ============ ADMIN ============
@app.get("/api/admin/audit-logs")
async def get_audit_logs(page: int = 1, per_page: int = 50, action: Optional[str] = None,
                         admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        if action:
            query = query.where(AuditLog.action == action)
        total_result = await db.execute(select(func.count(AuditLog.id)))
        total = total_result.scalar()
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        logs = result.scalars().all()
        return {"total": total, "page": page, "per_page": per_page,
                "logs": [{"id": log.id, "user_id": log.user_id, "action": log.action,
                         "resource": log.resource, "details": log.details, "success": log.success,
                         "created_at": log.created_at.isoformat() if log.created_at else None} for log in logs]}
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения логов")

@app.get("/api/admin/users")
async def get_users(page: int = 1, per_page: int = 50,
                    admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        total_result = await db.execute(select(func.count(User.id)))
        total = total_result.scalar()
        result = await db.execute(select(User).order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page))
        users = result.scalars().all()
        return {"total": total, "page": page, "per_page": per_page,
                "users": [{"id": u.id, "email": u.email, "full_name": u.full_name, "tier": u.subscription_tier,
                          "is_verified": u.is_verified, "is_active": u.is_active, "is_admin": u.is_admin,
                          "created_at": u.created_at.isoformat() if u.created_at else None} for u in users]}
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения пользователей")

@app.post("/api/admin/users/{user_id}/tier")
async def update_user_tier(user_id: int, tier: str = Form(...), expires: Optional[str] = Form(None),
                           admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        user.subscription_tier = tier
        if expires:
            user.subscription_expires = datetime.fromisoformat(expires)
        await db.commit()
        await log_audit(db=db, action="tier_changed", user_id=admin.id, resource="users",
                       resource_id=str(user_id), details=f"Changed to {tier}")
        return {"message": f"Подписка изменена на {tier}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update tier error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка изменения подписки")

# ============ HTML ROUTES ============
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "csp_nonce": request.state.csp_nonce, "domain": settings.DOMAIN})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/svetlana", response_class=HTMLResponse)
async def svetlana_page(request: Request):
    return templates.TemplateResponse("svetlana.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/contracts", response_class=HTMLResponse)
async def contracts_page(request: Request):
    return templates.TemplateResponse("contracts.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/finance", response_class=HTMLResponse)
async def finance_page(request: Request):
    return templates.TemplateResponse("finance.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/crm", response_class=HTMLResponse)
async def crm_page(request: Request):
    return templates.TemplateResponse("crm.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/marketplace", response_class=HTMLResponse)
async def marketplace_page(request: Request):
    return templates.TemplateResponse("marketplace.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/grants", response_class=HTMLResponse)
async def grants_page(request: Request):
    return templates.TemplateResponse("grants.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/achievements", response_class=HTMLResponse)
async def achievements_page(request: Request):
    return templates.TemplateResponse("achievements.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/marketplace/{slug}", response_class=HTMLResponse)
async def marketplace_profile_page(request: Request, slug: str):
    return templates.TemplateResponse("marketplace_profile.html", {"request": request, "csp_nonce": request.state.csp_nonce, "slug": slug})


# ============ WEBSOCKET ENDPOINTS ============
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(None)):
    user_id = None
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
        except JWTError:
            await websocket.close(code=4001, reason="Invalid token")
            return

    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive, handle ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "mark_read":
                # Handle mark notification as read
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)

@app.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket, token: str = Query(None)):
    """Admin dashboard real-time updates"""
    user_id = None
    is_admin = False
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if isinstance(user_id, str) and user_id.isdigit():
                user_id = int(user_id)
            # Verify admin status
            # Note: In production, verify against DB
        except JWTError:
            await websocket.close(code=4001, reason="Invalid token")
            return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


# ============ SMS API ============
@app.post("/api/sms/send")
@limiter.limit("20/minute")
async def send_sms_api(request: Request, phone: str = Form(..., max_length=50, regex=r"^\+7\d{10}$"),
                       message: str = Form(..., max_length=500),
                       current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Send SMS via SMS.ru"""
    try:
        if not settings.SMS_RU_API_KEY:
            raise HTTPException(status_code=503, detail="SMS.ru not configured")

        # Validate phone format
        if not phone.startswith("+7") or len(phone) != 12:
            raise HTTPException(status_code=400, detail="Phone must be in format +7XXXXXXXXXX")

        # Create log entry
        sms_log = SMSLog(user_id=current_user.id, phone=phone, message=message, status="pending")
        db.add(sms_log)
        await db.commit()
        await db.refresh(sms_log)

        # Send via SMS.ru
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://sms.ru/sms/send",
                params={
                    "api_id": settings.SMS_RU_API_KEY,
                    "to": phone,
                    "msg": message,
                    "json": 1,
                    "from": "MirSamoz"
                }
            )
            data = response.json()

            if data.get("status") == "OK":
                sms_id = list(data.get("sms", {}).keys())[0] if data.get("sms") else None
                sms_info = data.get("sms", {}).get(sms_id, {}) if sms_id else {}

                sms_log.status = "sent" if sms_info.get("status") == "OK" else "failed"
                sms_log.sms_ru_id = str(sms_info.get("sms_id", ""))
                sms_log.cost = float(data.get("balance", 0))
                sms_log.sent_at = datetime.now(timezone.utc)

                await db.commit()

                return {
                    "id": sms_log.id,
                    "status": sms_log.status,
                    "phone": phone,
                    "message": message,
                    "cost": sms_log.cost
                }
            else:
                sms_log.status = "failed"
                await db.commit()
                raise HTTPException(status_code=400, detail=data.get("status_text", "SMS.ru error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send SMS")

@app.get("/api/sms/history")
async def get_sms_history(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                         page: int = 1, per_page: int = 50):
    """Get SMS sending history"""
    try:
        query = select(SMSLog).where(SMSLog.user_id == current_user.id).order_by(SMSLog.created_at.desc())
        total_result = await db.execute(select(func.count(SMSLog.id)).where(SMSLog.user_id == current_user.id))
        total = total_result.scalar()

        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        logs = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "logs": [{
                "id": log.id,
                "phone": log.phone,
                "message": log.message,
                "status": log.status,
                "cost": log.cost,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                "created_at": log.created_at.isoformat() if log.created_at else None
            } for log in logs]
        }
    except Exception as e:
        logger.error(f"SMS history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SMS history")

@app.get("/api/sms/balance")
async def get_sms_balance(current_user: User = Depends(get_current_user)):
    """Get SMS.ru balance"""
    try:
        if not settings.SMS_RU_API_KEY:
            return {"balance": 0, "currency": "RUB", "status": "not_configured"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://sms.ru/my/balance",
                params={"api_id": settings.SMS_RU_API_KEY, "json": 1}
            )
            data = response.json()
            return {
                "balance": float(data.get("balance", 0)),
                "currency": "RUB",
                "status": data.get("status", "unknown")
            }
    except Exception as e:
        logger.error(f"SMS balance error: {e}")
        return {"balance": 0, "currency": "RUB", "status": "error"}

# ============ SEED DATA ============
async def seed_data(db: AsyncSession):
    result = await db.execute(select(User).where(User.email == "admin@мир-самозанятых.рф"))
    if not result.scalar_one_or_none():
        admin = User(email="admin@мир-самозанятых.рф", password_hash=get_password_hash("Admin123!"),
                    full_name="Администратор", is_verified=True, is_admin=True, subscription_tier="enterprise")
        db.add(admin)
    result = await db.execute(select(ContractTemplate))
    if not result.scalars().first():
        templates_data = [
            {"name": "Договор оказания услуг (физлицо)", "category": "services", "content": "ДОГОВОР № ___\nна оказание услуг\n\nг. ______ \"___\" ______ 20__ г.\n\nИсполнитель: [ФИО], ИНН [ИНН], самозанятый\nЗаказчик: [ФИО/Наименование], [Реквизиты]\n\n1. Предмет договора...", "is_premium": False},
            {"name": "Договор подряда (премиум)", "category": "contract", "content": "ДОГОВОР ПОДРЯДА № ___\n\n1. Подрядчик обязуется выполнить работы...", "is_premium": True},
            {"name": "Акт выполненных работ", "category": "act", "content": "АКТ\nвыполненных работ (оказанных услуг)\n\nк договору № ___ от \"___\" ______ 20__ г.\n\n1. Настоящий акт составлен о том, что...", "is_premium": False},
            {"name": "Коммерческое предложение (премиум)", "category": "commercial", "content": "КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ\n\nУважаемый [ИМЯ КЛИЕНТА]!\n\nПредлагаем услуги...", "is_premium": True},
        ]
        for t in templates_data:
            db.add(ContractTemplate(**t))
    await db.commit()
    logger.info("Seed data applied")

# ============ MAIN ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000,
                reload=settings.ENVIRONMENT == "development",
                log_level=settings.LOG_LEVEL.lower())
