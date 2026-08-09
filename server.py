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
import base64
import random
from datetime import datetime, timedelta, timezone, date
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
    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_SECRET_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    YANDEX_CLIENT_ID: str = ""
    YANDEX_CLIENT_SECRET: str = ""
    TELEGRAM_OAUTH_BOT: str = ""

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
from sqlalchemy import create_engine, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
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
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    clients = relationship("Client", back_populates="user")
    marketplace_profile = relationship("MarketplaceProfile", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")
    mfa = relationship("UserMFA", back_populates="user", uselist=False)

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




class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invoice_number = Column(String(100), unique=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    total_amount = Column(Float, default=0.0)
    status = Column(String(50), default="draft")
    due_date = Column(DateTime)
    yookassa_payment_id = Column(String(255))
    paid_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = relationship("User")
    client = relationship("Client")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    invoice = relationship("Invoice", back_populates="items")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default="card")
    status = Column(String(50), default="pending")
    yookassa_id = Column(String(255))
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    invoice = relationship("Invoice", back_populates="payments")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    unit = Column(String(50), default="шт")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User")

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


class UserMFA(Base):
    __tablename__ = "user_mfa"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    totp_secret = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=False)
    backup_codes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="mfa")

# ============ FASTAPI SETUP ============

# ============ BLOG MODELS ============

class BlogTag(Base):
    __tablename__ = 'blog_tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    slug = Column(String(60), unique=True, nullable=False, index=True)
    color = Column(String(7), default='#0D47A1')  # hex color
    created_at = Column(DateTime, default=datetime.utcnow)

class BlogPost(Base):
    __tablename__ = 'blog_posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(220), unique=True, nullable=False, index=True)
    excerpt = Column(Text, nullable=True)  # краткое описание
    content = Column(Text, nullable=False)
    cover_image = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='draft')  # draft, published, archived
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    meta_description = Column(String(300), nullable=True)
    meta_keywords = Column(String(300), nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User")
    comments = relationship("BlogComment", back_populates="post", cascade="all, delete-orphan")
    tags = relationship("BlogTag", secondary="blog_post_tags", back_populates="posts")

class BlogPostTag(Base):
    __tablename__ = 'blog_post_tags'
    post_id = Column(Integer, ForeignKey('blog_posts.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('blog_tags.id'), primary_key=True)

class BlogComment(Base):
    __tablename__ = 'blog_comments'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('blog_posts.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # null = anonymous/guest
    author_name = Column(String(100), nullable=True)  # для гостей
    author_email = Column(String(200), nullable=True)  # для гостей
    content = Column(Text, nullable=False)
    status = Column(String(20), default='pending')  # pending, approved, rejected, spam
    parent_id = Column(Integer, ForeignKey('blog_comments.id'), nullable=True)  # replies
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post = relationship("BlogPost", back_populates="comments")
    author = relationship("User")
    parent = relationship("BlogComment", remote_side=[id], backref="replies")


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
        # Always use SSL/TLS — never unencrypted connections
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
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

class AIError(Exception):
    """Custom exception for AI service errors"""
    pass

async def ask_ai(question: str, context: str = "", model: str = "anthropic/claude-3.5-sonnet") -> str:
    if not settings.OPENROUTER_API_KEY:
        raise AIError("OpenRouter API key not configured")
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
            if "choices" not in data or not data["choices"]:
                raise AIError(f"Invalid AI response: {data.get('error', 'Unknown error')}")
            return data["choices"][0]["message"]["content"]
    except AIError:
        raise
    except Exception as e:
        logger.error(f"AI error: {e}")
        raise AIError(f"Failed to get AI response: {str(e)}")

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
    description="Платформа для самозанятых — PDF/QR Edition v5.3",
    version="5.3.0",
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

async def get_current_user_optional(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        payload = await verify_token(token, db=db)
        user_id = int(payload.get("sub"))
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception:
        return None

def require_role(roles: list):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current_user
    return checker

def require_subscription(tier: str):
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
        # Сначала ищем в базе знаний
        knowledge = load_svetlana_knowledge()
        question_lower = question.lower()

        # 1. Проверяем quick_answers (точное совпадение ключевых слов)
        quick_answers = knowledge.get("quick_answers", {})
        for key, answer in quick_answers.items():
            if key in question_lower:
                return {"answer": answer, "confidence": 0.9, "source": "quick_answer"}

        # 2. Ищем по topics (по ключевым словам в заголовках и содержимом)
        topics = knowledge.get("topics", [])
        best_topic = None
        best_score = 0

        for topic in topics:
            topic_title = topic.get("title", "").lower()
            topic_content = topic.get("content", "").lower()
            topic_id = topic.get("id", "").lower()

            score = 0
            words = question_lower.split()
            for word in words:
                if len(word) > 2:  # Игнорируем короткие слова
                    if word in topic_title:
                        score += 3
                    if word in topic_content:
                        score += 1
                    if word in topic_id:
                        score += 2

            if category and topic.get("id") == category:
                score += 5  # Бонус за точное совпадение категории

            if score > best_score:
                best_score = score
                best_topic = topic

        # Если нашли релевантную тему с достаточным скором
        if best_topic and best_score >= 2:
            return {
                "answer": best_topic["content"],
                "confidence": min(best_score / 10, 1.0),
                "source": "knowledge_base",
                "topic": best_topic.get("title")
            }

        # 3. Если включен AI и есть API ключ — спрашиваем ИИ
        if use_ai and settings.OPENROUTER_API_KEY:
            context = ""
            if current_user:
                context = f"Пользователь: {current_user.full_name}, ИНН: {current_user.inn or 'не указан'}"
            try:
                ai_answer = await ask_ai(question, context=context)
                if ai_answer:
                    return {"answer": ai_answer, "confidence": 0.95, "source": "ai_openrouter"}
            except AIError:
                pass

        # 4. Fallback — умный ответ на основе тематики
        fallbacks = [
            "Извините, я пока не знаю ответа на этот вопрос. Попробуйте переформулировать или выберите категорию из списка.",
            "Интересный вопрос! Давайте уточним: вас интересует налоги, гранты, регистрация или что-то другое?",
            "Я специализируюсь на вопросах самозанятости. Могу рассказать о налогах, грантах, социальных контрактах, коворкингах, штрафах и льготных кредитах.",
        ]
        import random
        return {"answer": random.choice(fallbacks), "confidence": 0.0, "source": "fallback"}

    except Exception as e:
        logger.error(f"Svetlana error: {e}")
        return {"answer": "Извините, произошла ошибка. Попробуйте позже.", "confidence": 0, "source": "error"}
@app.get("/api/svetlana/categories")
async def get_svetlana_categories():
    try:
        knowledge = load_svetlana_knowledge()
        topics = knowledge.get("topics", [])
        return {
            "categories": [
                {"key": t["id"], "title": t["title"]} 
                for t in topics
            ]
        }
    except Exception as e:
        logger.error(f"Svetlana categories error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки категорий")
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

# ============ BLOG API ============

from pydantic import BaseModel, Field
from typing import Optional, List

class BlogTagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#0D47A1", max_length=7)

class BlogTagOut(BaseModel):
    id: int
    name: str
    slug: str
    color: str
    class Config:
        from_attributes = True

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    excerpt: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=50)
    cover_image: Optional[str] = None
    tag_ids: List[int] = Field(default_factory=list)
    meta_description: Optional[str] = Field(None, max_length=300)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")

class BlogPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    excerpt: Optional[str] = None
    content: Optional[str] = Field(None, min_length=50)
    cover_image: Optional[str] = None
    tag_ids: Optional[List[int]] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")

class BlogPostOut(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    cover_image: Optional[str]
    author_id: int
    author_name: str
    status: str
    views: int
    likes: int
    tags: List[BlogTagOut]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class BlogCommentCreate(BaseModel):
    content: str = Field(..., min_length=2, max_length=2000)
    author_name: Optional[str] = Field(None, max_length=100)
    author_email: Optional[str] = Field(None, max_length=200)
    parent_id: Optional[int] = None

class BlogCommentOut(BaseModel):
    id: int
    post_id: int
    content: str
    author_name: Optional[str]
    author_email: Optional[str]
    status: str
    parent_id: Optional[int]
    created_at: datetime
    replies: List[dict] = Field(default_factory=list)
    class Config:
        from_attributes = True

import re
from slugify import slugify

def generate_slug(title: str, db: Session, model_class, existing_id: int = None) -> str:
    base_slug = slugify(title, max_length=200)
    slug = base_slug
    counter = 1
    while True:
        query = db.query(model_class).filter(model_class.slug == slug)
        if existing_id:
            query = query.filter(model_class.id != existing_id)
        if not query.first():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

# --- Blog Tags API ---


# ============ ADMIN SECURITY ENHANCEMENTS ============

import ipaddress
from datetime import timedelta

# Admin login attempts tracking (in-memory, for production use Redis)
_admin_login_attempts = {}
_admin_ip_whitelist = set()  # Configure in settings or database

class AdminLoginAttempt(Base):
    __tablename__ = 'admin_login_attempts'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(45), nullable=False, index=True)
    username = Column(String(100), nullable=True)
    success = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AdminIPWhitelist(Base):
    __tablename__ = 'admin_ip_whitelist'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(45), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

def check_admin_2fa(current_user: User):
    """Verify admin has 2FA enabled"""
    if current_user.role in ["admin", "moderator"]:
        # Check if user has MFA setup
        # This is a simplified check - in production check UserMFA table
        pass  # Implementation depends on existing 2FA structure

def check_ip_whitelist(ip_address: str, db: Session) -> bool:
    """Check if IP is in admin whitelist"""
    # If no whitelist configured, allow all (for initial setup)
    whitelist_count = db.query(AdminIPWhitelist).count()
    if whitelist_count == 0:
        return True

    return db.query(AdminIPWhitelist).filter(AdminIPWhitelist.ip_address == ip_address).first() is not None

def check_admin_lockout(ip_address: str, db: Session) -> tuple:
    """Check if IP is locked out due to failed attempts"""
    # Count failed attempts in last 30 minutes
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    attempts = db.query(AdminLoginAttempt).filter(
        AdminLoginAttempt.ip_address == ip_address,
        AdminLoginAttempt.success == False,
        AdminLoginAttempt.created_at > cutoff
    ).count()

    if attempts >= 3:
        # Check if there's a successful login after the failures
        last_success = db.query(AdminLoginAttempt).filter(
            AdminLoginAttempt.ip_address == ip_address,
            AdminLoginAttempt.success == True,
            AdminLoginAttempt.created_at > cutoff
        ).order_by(AdminLoginAttempt.created_at.desc()).first()

        if not last_success:
            return False, f"IP заблокирован после {attempts} неудачных попыток. Попробуйте через 30 минут."

    return True, None

def record_admin_login(ip_address: str, username: str, success: bool, db: Session):
    """Record admin login attempt"""
    attempt = AdminLoginAttempt(
        ip_address=ip_address,
        username=username,
        success=success
    )
    db.add(attempt)
    db.commit()

# ============ ENHANCED ADMIN API ============

@app.get("/api/admin/dashboard")
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin dashboard with key metrics"""
    require_role(current_user, ["admin", "moderator"])

    # IP whitelist check
    client_ip = request.client.host
    if not check_ip_whitelist(client_ip, db):
        raise HTTPException(status_code=403, detail="Доступ запрещён: IP не в белом списке")

    # Check lockout
    allowed, message = check_admin_lockout(client_ip, db)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)

    # Gather metrics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    new_users_today = db.query(User).filter(
        User.created_at > datetime.now(timezone.utc) - timedelta(days=1)
    ).count()

    total_transactions = db.query(Transaction).count()
    total_revenue = db.query(Transaction).filter(Transaction.type == "income").with_entities(func.sum(Transaction.amount)).scalar() or 0

    total_contracts = db.query(SignedContract).count()
    signed_contracts = db.query(SignedContract).filter(SignedContract.status == "signed").count()

    total_posts = db.query(BlogPost).count()
    published_posts = db.query(BlogPost).filter(BlogPost.status == "published").count()

    pending_comments = db.query(BlogComment).filter(BlogComment.status == "pending").count()

    # Recent audit logs
    recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all()

    # Login attempts
    recent_attempts = db.query(AdminLoginAttempt).order_by(AdminLoginAttempt.created_at.desc()).limit(10).all()

    log_audit(db, current_user.id, "admin_dashboard_accessed", f"IP: {client_ip}", request)

    return {
        "metrics": {
            "users": {"total": total_users, "active": active_users, "new_today": new_users_today},
            "finance": {"transactions": total_transactions, "total_revenue": float(total_revenue)},
            "contracts": {"total": total_contracts, "signed": signed_contracts},
            "blog": {"posts": total_posts, "published": published_posts, "pending_comments": pending_comments},
        },
        "recent_audit_logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat()
            }
            for log in recent_logs
        ],
        "recent_login_attempts": [
            {
                "ip": attempt.ip_address,
                "username": attempt.username,
                "success": attempt.success,
                "time": attempt.created_at.isoformat()
            }
            for attempt in recent_attempts
        ],
        "security": {
            "ip_whitelist_enabled": db.query(AdminIPWhitelist).count() > 0,
            "your_ip": client_ip,
            "session_info": "Активна"
        }
    }

@app.get("/api/admin/security/logs")
async def admin_security_logs(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detailed security audit logs with filtering"""
    require_role(current_user, ["admin", "moderator"])

    query = db.query(AuditLog)
    if action_type:
        query = query.filter(AuditLog.action.ilike(f"%{action_type}%"))

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    log_audit(db, current_user.id, "admin_security_logs_viewed", f"Page: {page}, Filter: {action_type}", request)

    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }

@app.post("/api/admin/security/ip-whitelist")
async def add_ip_whitelist(
    request: Request,
    ip_address: str = Form(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add IP to admin whitelist"""
    require_role(current_user, ["admin"])

    # Validate IP
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный IP-адрес")

    # Check if already exists
    existing = db.query(AdminIPWhitelist).filter(AdminIPWhitelist.ip_address == ip_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="IP уже в белом списке")

    whitelist_entry = AdminIPWhitelist(
        ip_address=ip_address,
        description=description,
        created_by=current_user.id
    )
    db.add(whitelist_entry)
    db.commit()

    log_audit(db, current_user.id, "admin_ip_whitelist_added", f"IP: {ip_address}", request)

    return {"message": f"IP {ip_address} добавлен в белый список"}

@app.delete("/api/admin/security/ip-whitelist/{ip_id}")
async def remove_ip_whitelist(
    ip_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove IP from whitelist"""
    require_role(current_user, ["admin"])

    entry = db.query(AdminIPWhitelist).filter(AdminIPWhitelist.id == ip_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    db.delete(entry)
    db.commit()

    log_audit(db, current_user.id, "admin_ip_whitelist_removed", f"IP ID: {ip_id}", request)

    return {"message": "IP удалён из белого списка"}

@app.get("/api/admin/security/ip-whitelist")
async def list_ip_whitelist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List whitelisted IPs"""
    require_role(current_user, ["admin", "moderator"])

    entries = db.query(AdminIPWhitelist).all()
    return {
        "whitelist": [
            {
                "id": e.id,
                "ip_address": e.ip_address,
                "description": e.description,
                "created_by": e.created_by,
                "created_at": e.created_at.isoformat()
            }
            for e in entries
        ]
    }

@app.post("/api/admin/users/{user_id}/block")
async def block_user(
    user_id: int,
    request: Request,
    reason: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Block/unblock user"""
    require_role(current_user, ["admin", "moderator"])

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя заблокировать себя")

    user.is_active = False
    db.commit()

    log_audit(db, current_user.id, "user_blocked", f"User: {user_id}, Reason: {reason}", request)

    return {"message": f"Пользователь {user.email} заблокирован", "reason": reason}

@app.post("/api/admin/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unblock user"""
    require_role(current_user, ["admin", "moderator"])

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.is_active = True
    db.commit()

    log_audit(db, current_user.id, "user_unblocked", f"User: {user_id}", request)

    return {"message": f"Пользователь {user.email} разблокирован"}

@app.get("/api/admin/comments/pending")
async def list_pending_comments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List pending blog comments for moderation"""
    require_role(current_user, ["admin", "moderator", "support"])

    query = db.query(BlogComment).filter(BlogComment.status == "pending")
    total = query.count()
    comments = query.order_by(BlogComment.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "comments": [
            {
                "id": c.id,
                "post_id": c.post_id,
                "post_title": c.post.title if c.post else "—",
                "author_name": c.author_name,
                "author_email": c.author_email,
                "content": c.content,
                "created_at": c.created_at.isoformat()
            }
            for c in comments
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }


@app.post("/api/blog/tags", response_model=BlogTagOut)
async def create_blog_tag(
    tag: BlogTagCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_role(current_user, ["admin", "moderator"])
    slug = slugify(tag.name, max_length=60)
    db_tag = BlogTag(name=tag.name, slug=slug, color=tag.color)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    log_audit(db, current_user.id, "blog_tag_created", f"Tag: {tag.name}", request)
    return db_tag

@app.get("/api/blog/tags", response_model=List[BlogTagOut])
async def list_blog_tags(db: AsyncSession = Depends(get_db)):
    return db.query(BlogTag).order_by(BlogTag.name).all()

# --- Blog Posts API ---

@app.post("/api/blog/posts", response_model=BlogPostOut)
async def create_blog_post(
    post: BlogPostCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_role(current_user, ["admin", "moderator", "support"])
    slug = generate_slug(post.title, db, BlogPost)
    published_at = datetime.now(timezone.utc) if post.status == "published" else None

    db_post = BlogPost(
        title=post.title,
        slug=slug,
        excerpt=post.excerpt,
        content=post.content,
        cover_image=post.cover_image,
        author_id=current_user.id,
        status=post.status,
        meta_description=post.meta_description,
        meta_keywords=post.meta_keywords,
        published_at=published_at
    )
    db.add(db_post)
    db.flush()

    # Attach tags
    if post.tag_ids:
        tags = db.query(BlogTag).filter(BlogTag.id.in_(post.tag_ids)).all()
        db_post.tags = tags

    db.commit()
    db.refresh(db_post)
    log_audit(db, current_user.id, "blog_post_created", f"Post: {post.title}", request)
    return db_post

@app.get("/api/blog/posts")
async def list_blog_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    tag: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = "published",
    db: AsyncSession = Depends(get_db)
):
    query = db.query(BlogPost)

    if status:
        query = query.filter(BlogPost.status == status)

    if tag:
        query = query.join(BlogPost.tags).filter(BlogTag.slug == tag)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (BlogPost.title.ilike(search_filter)) |
            (BlogPost.excerpt.ilike(search_filter)) |
            (BlogPost.content.ilike(search_filter))
        )

    total = query.count()
    posts = query.order_by(BlogPost.published_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "posts": [{
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "excerpt": p.excerpt,
            "cover_image": p.cover_image,
            "author_name": p.author.name if p.author else "Аноним",
            "status": p.status,
            "views": p.views,
            "likes": p.likes,
            "tags": [{"id": t.id, "name": t.name, "slug": t.slug, "color": t.color} for t in p.tags],
            "published_at": p.published_at.isoformat() if p.published_at else None,
            "created_at": p.created_at.isoformat(),
            "comment_count": len([c for c in p.comments if c.status == "approved"])
        } for p in posts],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }

@app.get("/api/blog/posts/{slug}")
async def get_blog_post(slug: str, db: AsyncSession = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    # Increment views
    post.views += 1
    db.commit()

    # Get related posts (same tags)
    tag_ids = [t.id for t in post.tags]
    related = []
    if tag_ids:
        related = db.query(BlogPost).join(BlogPost.tags).filter(
            BlogTag.id.in_(tag_ids),
            BlogPost.id != post.id,
            BlogPost.status == "published"
        ).distinct().limit(3).all()

    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "excerpt": post.excerpt,
        "content": post.content,
        "cover_image": post.cover_image,
        "author_id": post.author_id,
        "author_name": post.author.name if post.author else "Аноним",
        "status": post.status,
        "views": post.views,
        "likes": post.likes,
        "tags": [{"id": t.id, "name": t.name, "slug": t.slug, "color": t.color} for t in post.tags],
        "meta_description": post.meta_description,
        "meta_keywords": post.meta_keywords,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
        "related_posts": [{
            "id": r.id,
            "title": r.title,
            "slug": r.slug,
            "excerpt": r.excerpt,
            "cover_image": r.cover_image
        } for r in related]
    }

@app.put("/api/blog/posts/{post_id}", response_model=BlogPostOut)
async def update_blog_post(
    post_id: int,
    post_update: BlogPostUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_role(current_user, ["admin", "moderator", "support"])
    db_post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    # Only author or admin can edit
    if db_post.author_id != current_user.id and current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Нет прав на редактирование")

    update_data = post_update.model_dump(exclude_unset=True)

    if "title" in update_data and update_data["title"] != db_post.title:
        update_data["slug"] = generate_slug(update_data["title"], db, BlogPost, db_post.id)

    if "status" in update_data:
        if update_data["status"] == "published" and not db_post.published_at:
            update_data["published_at"] = datetime.now(timezone.utc)

    if "tag_ids" in update_data and update_data["tag_ids"] is not None:
        tags = db.query(BlogTag).filter(BlogTag.id.in_(update_data["tag_ids"])).all()
        db_post.tags = tags
        del update_data["tag_ids"]

    for key, value in update_data.items():
        setattr(db_post, key, value)

    db.commit()
    db.refresh(db_post)
    log_audit(db, current_user.id, "blog_post_updated", f"Post ID: {post_id}", request)
    return db_post

@app.delete("/api/blog/posts/{post_id}")
async def delete_blog_post(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_role(current_user, ["admin", "moderator"])
    db_post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    db.delete(db_post)
    db.commit()
    log_audit(db, current_user.id, "blog_post_deleted", f"Post ID: {post_id}", request)
    return {"message": "Статья удалена"}

@app.post("/api/blog/posts/{post_id}/like")
async def like_blog_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    post.likes += 1
    db.commit()
    return {"likes": post.likes}

# --- Blog Comments API ---

@app.post("/api/blog/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    comment: BlogCommentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    # Auto-approve for authenticated users, pending for guests
    status = "approved" if current_user else "pending"

    db_comment = BlogComment(
        post_id=post_id,
        user_id=current_user.id if current_user else None,
        author_name=current_user.name if current_user else (comment.author_name or "Гость"),
        author_email=current_user.email if current_user else comment.author_email,
        content=comment.content,
        status=status,
        parent_id=comment.parent_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    if current_user:
        log_audit(db, current_user.id, "blog_comment_created", f"Post ID: {post_id}", request)

    return {
        "id": db_comment.id,
        "content": db_comment.content,
        "author_name": db_comment.author_name,
        "status": db_comment.status,
        "created_at": db_comment.created_at.isoformat()
    }

@app.get("/api/blog/posts/{post_id}/comments")
async def list_comments(
    post_id: int,
    status: Optional[str] = "approved",
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    query = db.query(BlogComment).filter(BlogComment.post_id == post_id)

    # Moderators can see all comments
    if not current_user or current_user.role not in ["admin", "moderator", "support"]:
        query = query.filter(BlogComment.status == "approved")
    elif status:
        query = query.filter(BlogComment.status == status)

    comments = query.order_by(BlogComment.created_at.desc()).all()

    # Build tree structure
    comment_map = {}
    root_comments = []

    for c in comments:
        c_data = {
            "id": c.id,
            "content": c.content,
            "author_name": c.author_name,
            "status": c.status,
            "parent_id": c.parent_id,
            "created_at": c.created_at.isoformat(),
            "replies": []
        }
        comment_map[c.id] = c_data
        if c.parent_id is None:
            root_comments.append(c_data)
        elif c.parent_id in comment_map:
            comment_map[c.parent_id]["replies"].append(c_data)

    return {"comments": root_comments, "total": len(comments)}

@app.put("/api/blog/comments/{comment_id}/status")
async def moderate_comment(
    comment_id: int,
    request: Request,
    status: str = Query(..., pattern="^(approved|rejected|spam)$"),
    current_user: User = Depends(get_current_user)
):
    require_role(current_user, ["admin", "moderator", "support"])
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    comment.status = status
    db.commit()
    log_audit(db, current_user.id, "blog_comment_moderated", f"Comment {comment_id} -> {status}", request)
    return {"message": f"Комментарий {status}"}

@app.delete("/api/blog/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_role(current_user, ["admin", "moderator", "support"])
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    db.delete(comment)
    db.commit()
    log_audit(db, current_user.id, "blog_comment_deleted", f"Comment ID: {comment_id}", request)
    return {"message": "Комментарий удалён"}


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

@app.get("/blog", response_class=HTMLResponse)
async def blog_list_page(request: Request):
    return templates.TemplateResponse("blog.html", {"request": request, "csp_nonce": request.state.csp_nonce})

@app.get("/blog/{slug}", response_class=HTMLResponse)

@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request, "csp_nonce": request.state.csp_nonce})


async def blog_post_page(request: Request, slug: str):
    return templates.TemplateResponse("blog_post.html", {"request": request, "csp_nonce": request.state.csp_nonce, "slug": slug})

# ============ BLOG SEED DATA ============

@app.get("/api/blog/seed")
async def seed_blog_data(db: AsyncSession = Depends(get_db)):
    """Seed blog with sample data for demonstration"""
    if db.query(BlogPost).first():
        return {"message": "Блог уже заполнен"}

    # Create tags
    tags_data = [
        {"name": "НПД", "slug": "npd", "color": "#0D47A1"},
        {"name": "Налоги", "slug": "nalogi", "color": "#E91E63"},
        {"name": "Бизнес", "slug": "biznes", "color": "#43A047"},
        {"name": "CRM", "slug": "crm", "color": "#FF8C00"},
        {"name": "Гранты", "slug": "granty", "color": "#9C27B0"},
        {"name": "Советы", "slug": "sovety", "color": "#00BCD4"},
    ]

    tags = []
    for t in tags_data:
        tag = BlogTag(name=t["name"], slug=t["slug"], color=t["color"])
        db.add(tag)
        db.flush()
        tags.append(tag)

    # Sample posts
    posts_data = [
        {
            "title": "Как самозанятому правильно платить налоги в 2026 году",
            "excerpt": "Полный гид по налогу на профессиональный доход: ставки, вычеты, сроки и типичные ошибки.",
            "content": """Налог на профессиональный доход (НПД) — специальный налоговый режим для самозанятых граждан. В 2026 году действуют следующие ставки:

**4%** — при доходе от физических лиц
**6%** — при доходе от юридических лиц и ИП

Важные изменения 2026 года:
- Налоговый вычет 10 000 ₽ продлён
- Новые категории деятельности добавлены
- Упрощённая отчётность через приложение «Мой налог»

Чтобы не ошибиться:
1. Всегда формируйте чеки через приложение
2. Следите за лимитом дохода 2,4 млн ₽/год
3. Используйте налоговый вычет с умом
4. Проверяйте ИНН плательщика через наш сервис
5. Сохраняйте все чеки минимум 3 года

Наша платформа «Мир Самозанятых» помогает автоматизировать расчёт налогов и напоминает о сроках уплаты.""",
            "tags": [0, 1],
            "views": 1250,
            "likes": 45
        },
        {
            "title": "5 инструментов CRM для самозанятых: бесплатно и эффективно",
            "excerpt": "Обзор лучших CRM-систем, которые помогут организовать работу с клиентами без затрат.",
            "content": """CRM-система — must-have для любого самозанятого, работающего с клиентами. Вот топ-5 бесплатных решений:

1. **Битрикс24** — бесплатно до 12 пользователей, полный функционал
2. **МойСклад** — идеально для торговли и складского учёта
3. **YCLIENTS** — специализировано для сферы услуг
4. **Google Таблицы** — простое начало, бесплатно навсегда
5. **Наша встроенная CRM** — интегрирована с налоговым калькулятором и договорами

Ключевые функции CRM для самозанятых:
- База клиентов с историей взаимодействий
- История сделок и статусы
- Напоминания о задачах и встречах
- Автоматические отчёты по продажам
- Интеграция с мессенджерами

Начните с простого — даже Excel-таблица лучше, чем хаос в голове. Постепенно переходите на специализированные решения.""",
            "tags": [3, 5],
            "views": 890,
            "likes": 32
        },
        {
            "title": "Гранты для самозанятых в 2026: где искать и как получить",
            "excerpt": "Обзор федеральных и региональных программ поддержки самозанятых граждан.",
            "content": """В 2026 году самозанятые могут претендовать на несколько типов грантов:

**Федеральные программы:**
- Грант на развитие бизнеса до 500 000 ₽
- Социальный контракт для малоимущих
- Цифровые гранты для IT-проектов

**Региональные программы:**
- Москва: «Самозанятый Москвы» — до 300 000 ₽
- Санкт-Петербург: «Свой бизнес» — консультации + финансирование
- Регионы: через Центры занятости населения

Как подготовить заявку:
1. Составьте чёткий бизнес-план с цифрами
2. Подтвердите статус самозанятого (выписка из ФНС)
3. Убедитесь в отсутствии задолженностей
4. Напишите мотивационное письмо
5. Подготовьте портфолио выполненных работ

Используйте наш раздел «Гранты» — там собраны актуальные программы с фильтрацией по региону и сумме.""",
            "tags": [4, 5],
            "views": 2100,
            "likes": 78
        },
        {
            "title": "Как оформить договор ГПД: шаблоны и типичные ошибки",
            "excerpt": "Пошаговое руководство по составлению договора гражданско-правового характера для самозанятых.",
            "content": """Договор ГПД — основной документ для самозанятого при работе с клиентами. Разберём ключевые моменты:

**Обязательные пункты договора:**
1. Предмет договора (что именно выполняется)
2. Сроки выполнения работ
3. Стоимость и порядок оплаты
4. Порядок приёмки результата
5. Ответственность сторон
6. Форс-мажорные обстоятельства

**Типичные ошибки:**
- Отсутствие сроков — ведёт к бесконечным доработкам
- Неопределённая стоимость — споры при оплате
- Отсутствие порядка приёмки — клиент не принимает работу
- Нет ответственности — невозможно взыскать убытки

Наша платформа предоставляет готовые шаблоны ГПД, счетов и актов выполненных работ. Все документы составлены юристами с учётом специфики самозанятых.""",
            "tags": [2, 5],
            "views": 1560,
            "likes": 56
        },
        {
            "title": "Маркетплейс для самозанятых: как найти первых клиентов",
            "excerpt": "Стратегии привлечения клиентов через маркетплейс и личный бренд.",
            "content": """Наш маркетплейс «Мир Самозанятых» — это площадка, где заказчики находят исполнителей. Как выделиться:

**Оформление профиля:**
- Профессиональное фото или логотип
- Подробное описание услуг с ценами
- Портфолио выполненных работ
- Отзывы первых клиентов

**Привлечение клиентов:**
1. Разместите 3-5 примеров работ
2. Установите конкурентные цены
3. Отвечайте на запросы быстро (в течение часа)
4. Просите довольных клиентов оставить отзыв
5. Регулярно обновляйте портфолио

**Личный бренд:**
- Ведите блог на нашей платформе
- Делитесь экспертизой в соцсетях
- Участвуйте в обсуждениях и отвечайте на вопросы

Первые клиенты — самые сложные. Не бойтесь начинать с небольших проектов и низких цен. Главное — собрать портфолио и отзывы.""",
            "tags": [2, 5],
            "views": 670,
            "likes": 23
        },
    ]

    for p_data in posts_data:
        post = BlogPost(
            title=p_data["title"],
            slug=slugify(p_data["title"], max_length=200),
            excerpt=p_data["excerpt"],
            content=p_data["content"],
            author_id=1,
            status="published",
            published_at=datetime.now(timezone.utc),
            views=p_data.get("views", 0),
            likes=p_data.get("likes", 0)
        )
        db.add(post)
        db.flush()

        # Attach tags
        for tag_idx in p_data["tags"]:
            if tag_idx < len(tags):
                post.tags.append(tags[tag_idx])

    db.commit()
    return {"message": f"Создано {len(posts_data)} статей и {len(tags_data)} тегов"}




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

    # Origin check for production
    if settings.ENVIRONMENT == "production":
        allowed_origins = [f"https://{settings.DOMAIN}", f"https://www.{settings.DOMAIN}"]
        origin = websocket.headers.get("origin", "")
        if origin not in allowed_origins:
            await websocket.close(code=4002, reason="Invalid origin")
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

    # Origin check for production
    if settings.ENVIRONMENT == "production":
        allowed_origins = [f"https://{settings.DOMAIN}", f"https://www.{settings.DOMAIN}"]
        origin = websocket.headers.get("origin", "")
        if origin not in allowed_origins:
            await websocket.close(code=4002, reason="Invalid origin")
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
@limiter.limit("30/minute")
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


# ============ PDF / QR GENERATION ============
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
import io

# Register Russian font (try system fonts)
try:
    pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    RUSSIAN_FONT = 'DejaVu'
except:
    try:
        pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
        RUSSIAN_FONT = 'Arial'
    except:
        RUSSIAN_FONT = 'Helvetica'



# ============ SALES MODULE API ============

class InvoiceCreate(BaseModel):
    client_id: int
    due_date: Optional[date] = None
    notes: Optional[str] = None
    items: List[dict] = []

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None

class PaymentCreate(BaseModel):
    amount: float
    payment_method: str = "card"

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    unit: str = "шт"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None

@app.get("/api/sales/products")
async def list_products(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.user_id == current_user.id, Product.is_active == True).order_by(Product.name))
    products = result.scalars().all()
    return [{"id": p.id, "name": p.name, "description": p.description, "price": p.price, "unit": p.unit, "is_active": p.is_active, "created_at": p.created_at.isoformat() if p.created_at else None} for p in products]

@app.post("/api/sales/products")
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_product = Product(user_id=current_user.id, name=product.name, description=product.description, price=product.price, unit=product.unit)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    await log_audit(db=db, action="product_created", user_id=current_user.id, details=f"Product: {product.name}")
    return {"id": db_product.id, "name": db_product.name, "price": db_product.price}

@app.put("/api/sales/products/{product_id}")
async def update_product(product_id: int, product: ProductUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    for key, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)
    await db.commit()
    return {"id": db_product.id, "name": db_product.name, "price": db_product.price}

@app.delete("/api/sales/products/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    await db.delete(db_product)
    await db.commit()
    return {"message": "Услуга удалена"}

@app.get("/api/sales/invoices")
async def list_invoices(status: Optional[str] = None, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=50), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Invoice).where(Invoice.user_id == current_user.id)
    if status:
        query = query.where(Invoice.status == status)
    total = await db.scalar(select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id))
    result = await db.execute(query.order_by(Invoice.created_at.desc()).offset((page - 1) * per_page).limit(per_page))
    invoices = result.scalars().all()
    return {"invoices": [{"id": i.id, "invoice_number": i.invoice_number, "client_id": i.client_id, "total_amount": i.total_amount, "status": i.status, "due_date": i.due_date.isoformat() if i.due_date else None, "paid_at": i.paid_at.isoformat() if i.paid_at else None, "created_at": i.created_at.isoformat() if i.created_at else None} for i in invoices], "pagination": {"page": page, "per_page": per_page, "total": total, "total_pages": (total + per_page - 1) // per_page}}

@app.post("/api/sales/invoices")
async def create_invoice(invoice: InvoiceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc)
    count = await db.scalar(select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id, Invoice.created_at >= today.replace(hour=0, minute=0, second=0, microsecond=0)))
    invoice_number = f"СЧ-{current_user.id}-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    total = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in invoice.items)
    db_invoice = Invoice(user_id=current_user.id, invoice_number=invoice_number, client_id=invoice.client_id, total_amount=total, due_date=datetime.combine(invoice.due_date, datetime.min.time()).replace(tzinfo=timezone.utc) if invoice.due_date else None, notes=invoice.notes, status="draft")
    db.add(db_invoice)
    await db.flush()
    for item in invoice.items:
        db_item = InvoiceItem(invoice_id=db_invoice.id, description=item.get("description", ""), quantity=item.get("quantity", 1), unit_price=item.get("unit_price", 0), total_price=item.get("quantity", 1) * item.get("unit_price", 0))
        db.add(db_item)
    await db.commit()
    await db.refresh(db_invoice)
    await log_audit(db=db, action="invoice_created", user_id=current_user.id, details=f"Invoice: {invoice_number}, Amount: {total}")
    return {"id": db_invoice.id, "invoice_number": db_invoice.invoice_number, "total_amount": db_invoice.total_amount, "status": db_invoice.status}

@app.get("/api/sales/invoices/{invoice_id}")
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    items_result = await db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id))
    items = items_result.scalars().all()
    payments_result = await db.execute(select(Payment).where(Payment.invoice_id == invoice_id))
    payments = payments_result.scalars().all()
    return {"id": invoice.id, "invoice_number": invoice.invoice_number, "client_id": invoice.client_id, "total_amount": invoice.total_amount, "status": invoice.status, "due_date": invoice.due_date.isoformat() if invoice.due_date else None, "notes": invoice.notes, "yookassa_payment_id": invoice.yookassa_payment_id, "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None, "created_at": invoice.created_at.isoformat() if invoice.created_at else None, "items": [{"id": i.id, "description": i.description, "quantity": i.quantity, "unit_price": i.unit_price, "total_price": i.total_price} for i in items], "payments": [{"id": p.id, "amount": p.amount, "status": p.status, "payment_method": p.payment_method, "paid_at": p.paid_at.isoformat() if p.paid_at else None} for p in payments]}

@app.put("/api/sales/invoices/{invoice_id}")
async def update_invoice(invoice_id: int, invoice_update: InvoiceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    for key, value in invoice_update.model_dump(exclude_unset=True).items():
        if key == "due_date" and value:
            value = datetime.combine(value, datetime.min.time()).replace(tzinfo=timezone.utc)
        setattr(invoice, key, value)
    await db.commit()
    return {"id": invoice.id, "status": invoice.status}

@app.delete("/api/sales/invoices/{invoice_id}")
async def delete_invoice(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    await db.delete(invoice)
    await db.commit()
    return {"message": "Счёт удалён"}

@app.post("/api/sales/invoices/{invoice_id}/send")
async def send_invoice(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Счёт уже отправлен или оплачен")
    invoice.status = "sent"
    await db.commit()
    await log_audit(db=db, action="invoice_sent", user_id=current_user.id, details=f"Invoice: {invoice.invoice_number}")
    return {"message": "Счёт отправлен клиенту", "invoice_number": invoice.invoice_number}

@app.post("/api/sales/invoices/{invoice_id}/payments")
async def create_payment(invoice_id: int, payment: PaymentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    db_payment = Payment(invoice_id=invoice_id, amount=payment.amount, payment_method=payment.payment_method, status="pending")
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    payments_result = await db.execute(select(func.sum(Payment.amount)).where(Payment.invoice_id == invoice_id, Payment.status == "completed"))
    total_paid = payments_result.scalar() or 0
    if total_paid >= invoice.total_amount:
        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
        await db.commit()
    await log_audit(db=db, action="payment_created", user_id=current_user.id, details=f"Invoice: {invoice.invoice_number}, Amount: {payment.amount}")
    return {"id": db_payment.id, "amount": db_payment.amount, "status": db_payment.status}

@app.get("/api/sales/invoices/{invoice_id}/payments")
async def list_payments(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == current_user.id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    payments_result = await db.execute(select(Payment).where(Payment.invoice_id == invoice_id).order_by(Payment.created_at.desc()))
    payments = payments_result.scalars().all()
    return [{"id": p.id, "amount": p.amount, "status": p.status, "payment_method": p.payment_method, "paid_at": p.paid_at.isoformat() if p.paid_at else None, "created_at": p.created_at.isoformat() if p.created_at else None} for p in payments]

@app.get("/api/sales/stats")
async def sales_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_invoices = await db.scalar(select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id))
    total_revenue = await db.scalar(select(func.sum(Invoice.total_amount)).where(Invoice.user_id == current_user.id, Invoice.status == "paid")) or 0
    pending_amount = await db.scalar(select(func.sum(Invoice.total_amount)).where(Invoice.user_id == current_user.id, Invoice.status.in_(["sent", "draft"]))) or 0
    overdue = await db.scalar(select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id, Invoice.status == "sent", Invoice.due_date < datetime.now(timezone.utc)))
    return {"total_invoices": total_invoices, "total_revenue": float(total_revenue), "pending_amount": float(pending_amount), "overdue_invoices": overdue}
# ============ CONTRACT TEMPLATES DATA ============

CONTRACT_TEMPLATES = {
    "gpd": {
        "name": "Договор ГПД (гражданско-правовой)",
        "description": "Стандартный договор подряда/оказания услуг для самозанятых",
        "fields": ["contractor_name", "contractor_inn", "client_name", "client_inn", "subject", "price", "deadline", "payment_terms"]
    },
    "invoice": {
        "name": "Счёт на оплату",
        "description": "Счёт для юридических лиц и ИП с QR-кодом",
        "fields": ["seller_name", "seller_inn", "buyer_name", "buyer_inn", "services", "total", "bank_account", "bank_bik"]
    },
    "act": {
        "name": "Акт выполненных работ",
        "description": "Акт приёмки-передачи выполненных работ/услуг",
        "fields": ["contractor_name", "contractor_inn", "client_name", "client_inn", "works_description", "total", "act_date"]
    },
    "npd_receipt": {
        "name": "Чек самозанятого (НПД)",
        "description": "Чек по налогу на профессиональный доход",
        "fields": ["seller_name", "seller_inn", "buyer_name", "buyer_inn", "service_name", "amount", "tax_amount", "receipt_date"]
    }
}

# ============ E-SIGNATURE (Simple Electronic Signature per Civil Code Art. 160) ============

import hashlib
import hmac
from datetime import datetime

def generate_simple_signature(contract_data: dict, user_id: int, secret: str = None) -> dict:
    """Generate simple electronic signature per Russian Civil Code Article 160"""
    if secret is None:
        secret = settings.SECRET_KEY

    # Create canonical representation
    canonical = json.dumps(contract_data, sort_keys=True, ensure_ascii=False)
    timestamp = datetime.now(timezone.utc).isoformat()

    # Generate signature
    sig_payload = f"{user_id}:{timestamp}:{canonical}"
    signature = hmac.new(
        secret.encode(),
        sig_payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return {
        "signature": signature,
        "timestamp": timestamp,
        "algorithm": "HMAC-SHA256",
        "type": "simple_electronic_signature",
        "legal_basis": "ГК РФ ст. 160 (простая электронная подпись)",
        "signer_id": user_id
    }

def verify_simple_signature(contract_data: dict, signature_data: dict, secret: str = None) -> bool:
    """Verify simple electronic signature"""
    if secret is None:
        secret = settings.SECRET_KEY

    canonical = json.dumps(contract_data, sort_keys=True, ensure_ascii=False)
    sig_payload = f"{signature_data['signer_id']}:{signature_data['timestamp']}:{canonical}"
    expected = hmac.new(
        secret.encode(),
        sig_payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature_data['signature'])

# ============ ENHANCED PDF GENERATION ============

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import qrcode
import io

def generate_contract_pdf(template_type: str, data: dict, signature: dict = None) -> bytes:
    """Generate professional PDF contract with optional e-signature and QR code"""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'ContractTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=HexColor('#0D47A1'),
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'ContractHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        textColor=HexColor('#1565C0'),
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'ContractBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=8
    )

    footer_style = ParagraphStyle(
        'ContractFooter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#64748B'),
        alignment=TA_CENTER
    )

    story = []

    # Header
    story.append(Paragraph(f"<b>МИР САМОЗАНЯТЫХ</b>", title_style))
    story.append(Spacer(1, 5))

    template_info = CONTRACT_TEMPLATES.get(template_type, {})
    story.append(Paragraph(f"<b>{template_info.get('name', 'ДОКУМЕНТ')}</b>", title_style))
    story.append(Spacer(1, 20))

    # Document info table
    doc_info = [
        ["Дата создания:", datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")],
        ["Уникальный номер:", f"MS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{hashlib.md5(str(data).encode()).hexdigest()[:8].upper()}"],
    ]
    if signature:
        doc_info.append(["Электронная подпись:", "✓ Подписано простой электронной подписью"])
        doc_info.append(["Дата подписи:", signature.get('timestamp', '-')])
        doc_info.append(["Основание:", "ГК РФ ст. 160"])

    doc_table = Table(doc_info, colWidths=[50*mm, 110*mm])
    doc_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#374151')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#0D47A1')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(doc_table)
    story.append(Spacer(1, 20))

    # Content based on template type
    if template_type == "gpd":
        story.append(Paragraph("<b>1. ПРЕДМЕТ ДОГОВОРА</b>", heading_style))
        story.append(Paragraph(f"Исполнитель <b>{data.get('contractor_name', '—')}</b> (ИНН: {data.get('contractor_inn', '—')}) обязуется выполнить для Заказчика <b>{data.get('client_name', '—')}</b> (ИНН: {data.get('client_inn', '—')}) следующие работы/услуги:", body_style))
        story.append(Paragraph(f"<i>{data.get('subject', '—')}</i>", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>2. СТОИМОСТЬ И ПОРЯДОК РАСЧЁТОВ</b>", heading_style))
        story.append(Paragraph(f"2.1. Общая стоимость работ составляет <b>{data.get('price', '—')} ₽</b>.", body_style))
        story.append(Paragraph(f"2.2. Порядок оплаты: {data.get('payment_terms', '100% по факту выполнения')}", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>3. СРОКИ ВЫПОЛНЕНИЯ</b>", heading_style))
        story.append(Paragraph(f"3.1. Работы подлежат выполнению в срок до <b>{data.get('deadline', '—')}</b>.", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>4. ПОДПИСИ СТОРОН</b>", heading_style))
        story.append(Paragraph("4.1. Настоящий договор составлен в простой письменной форме в соответствии с ГК РФ ст. 161.", body_style))
        story.append(Paragraph("4.2. Стороны подтверждают, что условия договора им понятны и они согласны с ними.", body_style))

    elif template_type == "invoice":
        story.append(Paragraph("<b>СЧЁТ НА ОПЛАТУ</b>", heading_style))
        story.append(Paragraph(f"Продавец: <b>{data.get('seller_name', '—')}</b> (ИНН: {data.get('seller_inn', '—')})", body_style))
        story.append(Paragraph(f"Покупатель: <b>{data.get('buyer_name', '—')}</b> (ИНН: {data.get('buyer_inn', '—')})", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>Реквизиты для оплаты:</b>", heading_style))
        story.append(Paragraph(f"Р/с: {data.get('bank_account', '—')}", body_style))
        story.append(Paragraph(f"БИК: {data.get('bank_bik', '—')}", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>Содержание услуг:</b>", heading_style))
        story.append(Paragraph(f"{data.get('services', '—')}", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph(f"<b>ИТОГО К ОПЛАТЕ: {data.get('total', '—')} ₽</b>", heading_style))

        # QR code for payment
        qr_data = f"ST00012|Name={data.get('seller_name', '')}|PersonalAcc={data.get('bank_account', '')}|BIC={data.get('bank_bik', '')}|PayeeINN={data.get('seller_inn', '')}|Sum={int(float(data.get('total', 0)) * 100)}|Purpose=Оплата по счету"
        qr = qrcode.make(qr_data)
        qr_buffer = io.BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>QR-код для быстрой оплаты:</b>", heading_style))
        story.append(Image(qr_buffer, width=40*mm, height=40*mm))
        story.append(Paragraph("Отсканируйте QR-код в мобильном банке для мгновенной оплаты", footer_style))

    elif template_type == "act":
        story.append(Paragraph("<b>АКТ ВЫПОЛНЕННЫХ РАБОТ (ОКАЗАННЫХ УСЛУГ)</b>", heading_style))
        story.append(Paragraph(f"Дата составления: <b>{data.get('act_date', datetime.now(timezone.utc).strftime("%d.%m.%Y"))}</b>", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph(f"Исполнитель: <b>{data.get('contractor_name', '—')}</b> (ИНН: {data.get('contractor_inn', '—')})", body_style))
        story.append(Paragraph(f"Заказчик: <b>{data.get('client_name', '—')}</b> (ИНН: {data.get('client_inn', '—')})", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>Выполненные работы/оказанные услуги:</b>", heading_style))
        story.append(Paragraph(f"{data.get('works_description', '—')}", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph(f"<b>Стоимость работ: {data.get('total', '—')} ₽</b></b>", heading_style))
        story.append(Paragraph("Стороны подтверждают, что работы выполнены в полном объёме, в срок и надлежащего качества. Претензий по объёму, качеству и срокам выполнения работ не имеют.", body_style))

    elif template_type == "npd_receipt":
        story.append(Paragraph("<b>ЧЕК НАЛОГА НА ПРОФЕССИОНАЛЬНЫЙ ДОХОД</b>", heading_style))
        story.append(Paragraph(f"Дата: <b>{data.get('receipt_date', datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M"))}</b>", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph(f"Продавец (самозанятый): <b>{data.get('seller_name', '—')}</b>", body_style))
        story.append(Paragraph(f"ИНН продавца: {data.get('seller_inn', '—')}", body_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"Покупатель: <b>{data.get('buyer_name', '—')}</b>", body_style))
        story.append(Paragraph(f"ИНН покупателя: {data.get('buyer_inn', '—')}", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph(f"Услуга/товар: <b>{data.get('service_name', '—')}</b>", body_style))
        story.append(Paragraph(f"Сумма: <b>{data.get('amount', '—')} ₽</b>", body_style))
        story.append(Paragraph(f"Налог НПД (4% или 6%): <b>{data.get('tax_amount', '—')} ₽</b>", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>ПРИМЕЧАНИЕ:</b> Данный чек сформирован в соответствии с ФЗ-422 и является подтверждением уплаты налога на профессиональный доход. Храните чек в течение 3 лет.", body_style))

    # Signature section
    if signature:
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#E2E8F0')))
        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>БЛОК ЭЛЕКТРОННОЙ ПОДПИСИ</b>", heading_style))
        story.append(Paragraph(f"Тип подписи: {signature.get('type', '—')}", body_style))
        story.append(Paragraph(f"Алгоритм: {signature.get('algorithm', '—')}", body_style))
        story.append(Paragraph(f"Дата подписания: {signature.get('timestamp', '-')}", body_style))
        story.append(Paragraph(f"Подписант ID: {signature.get('signer_id', '—')}", body_style))
        story.append(Paragraph(f"Правовое основание: {signature.get('legal_basis', '—')}", body_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"Хеш подписи: <font size=7 face='Courier'>{signature.get('signature', '—')[:64]}...</font>", body_style))
        story.append(Paragraph("<i>Данная простая электронная подпись признаётся равнозначной собственноручной подписи в соответствии с Гражданским кодексом РФ (статья 160).</i>", footer_style))
    else:
        story.append(Spacer(1, 30))
        story.append(Paragraph("<b>ПОДПИСИ СТОРОН:</b>", heading_style))
        story.append(Paragraph("Документ требует подписания. Используйте кнопку «Подписать электронной подписью» в личном кабинете.", body_style))

    # Footer
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#E2E8F0')))
    story.append(Paragraph("<i>Сформировано на платформе «Мир Самозанятых» (мир-самозанятых.рф)</i>", footer_style))
    story.append(Paragraph(f"<i>Документ ID: {hashlib.sha256(str(data).encode()).hexdigest()[:16].upper()}</i>", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ============ ENHANCED CONTRACT API ============

class ContractSignRequest(BaseModel):
    contract_id: int
    sign_data: dict = Field(default_factory=dict)

@app.get("/api/contracts/templates/v2")
async def list_contract_templates_v2():
    """List all available contract templates with fields"""
    return {
        "templates": [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"],
                "fields": value["fields"]
            }
            for key, value in CONTRACT_TEMPLATES.items()
        ]
    }

@app.post("/api/contracts/generate/v2")
async def generate_contract_v2(
    request: Request,
    template_type: str = Form(...),
    data: str = Form(...),  # JSON string
    sign: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate contract with optional e-signature"""
    if template_type not in CONTRACT_TEMPLATES:
        raise HTTPException(status_code=400, detail="Неизвестный тип шаблона")

    try:
        contract_data = json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Неверный формат данных")

    # Generate signature if requested
    signature = None
    if sign:
        signature = generate_simple_signature(contract_data, current_user.id)

    # Generate PDF
    pdf_bytes = generate_contract_pdf(template_type, contract_data, signature)

    # Save to database
    db_contract = SignedContract(
        user_id=current_user.id,
        template_type=template_type,
        contract_data=json.dumps(contract_data),
        signature_data=json.dumps(signature) if signature else None,
        pdf_content=pdf_bytes,
        status="signed" if signature else "draft"
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)

    log_audit(db, current_user.id, "contract_generated", f"Type: {template_type}, Signed: {sign}", request)

    return {
        "contract_id": db_contract.id,
        "template_type": template_type,
        "signed": sign,
        "signature_info": signature,
        "download_url": f"/api/contracts/{db_contract.id}/pdf",
        "qr_url": f"/api/contracts/{db_contract.id}/qr" if template_type == "invoice" else None
    }

@app.post("/api/contracts/{contract_id}/sign")
async def sign_contract(
    contract_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sign existing contract with simple electronic signature"""
    contract = db.query(SignedContract).filter(SignedContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")

    if contract.user_id != current_user.id and current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Нет прав на подписание")

    if contract.status == "signed":
        raise HTTPException(status_code=400, detail="Договор уже подписан")

    contract_data = json.loads(contract.contract_data)
    signature = generate_simple_signature(contract_data, current_user.id)

    # Regenerate PDF with signature
    pdf_bytes = generate_contract_pdf(contract.template_type, contract_data, signature)

    contract.signature_data = json.dumps(signature)
    contract.pdf_content = pdf_bytes
    contract.status = "signed"
    contract.updated_at = datetime.now(timezone.utc)
    db.commit()

    log_audit(db, current_user.id, "contract_signed", f"Contract ID: {contract_id}", request)

    return {
        "message": "Договор успешно подписан",
        "signature": signature,
        "legal_basis": "ГК РФ ст. 160 (простая электронная подпись)"
    }

@app.get("/api/contracts/{contract_id}/verify")
async def verify_contract_signature(contract_id: int, db: AsyncSession = Depends(get_db)):
    """Verify contract electronic signature"""
    contract = db.query(SignedContract).filter(SignedContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")

    if not contract.signature_data:
        return {"signed": False, "message": "Договор не подписан"}

    try:
        signature = json.loads(contract.signature_data)
        contract_data = json.loads(contract.contract_data)
        is_valid = verify_simple_signature(contract_data, signature)

        return {
            "signed": True,
            "valid": is_valid,
            "signature_info": {
                "type": signature.get("type"),
                "algorithm": signature.get("algorithm"),
                "timestamp": signature.get("timestamp"),
                "signer_id": signature.get("signer_id"),
                "legal_basis": signature.get("legal_basis")
            },
            "message": "Подпись действительна" if is_valid else "Подпись НЕ действительна"
        }
    except Exception as e:
        return {"signed": True, "valid": False, "message": f"Ошибка проверки: {str(e)}"}


@app.post("/api/auth/2fa/setup")
async def setup_2fa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id))
        mfa = result.scalar_one_or_none()
        if mfa and mfa.is_enabled:
            raise HTTPException(status_code=400, detail="2FA already enabled")

        secret = pyotp.random_base32()
        backup_codes = [secrets.token_hex(4) for _ in range(8)]
        hashed_backups = json.dumps([get_password_hash(code) for code in backup_codes])

        if not mfa:
            mfa = UserMFA(user_id=current_user.id, totp_secret=secret, backup_codes=hashed_backups)
            db.add(mfa)
        else:
            mfa.totp_secret = secret
            mfa.backup_codes = hashed_backups
            mfa.is_enabled = False

        await db.commit()
        await db.refresh(mfa)

        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=current_user.email or str(current_user.id), issuer_name="Мир Самозанятых")

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        qr_b64 = base64.b64encode(buffer.getvalue()).decode()
        return {"qr_code": f"data:image/png;base64,{qr_b64}", "secret": secret, "backup_codes": backup_codes, "message": "Save backup codes!"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA setup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup 2FA")

@app.post("/api/auth/2fa/verify")
async def verify_2fa_setup(code: str = Form(..., min_length=6, max_length=6),
                           current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id))
        mfa = result.scalar_one_or_none()
        if not mfa:
            raise HTTPException(status_code=400, detail="2FA not set up")
        if mfa.is_enabled:
            raise HTTPException(status_code=400, detail="2FA already enabled")

        totp = pyotp.TOTP(mfa.totp_secret)
        if not totp.verify(code, valid_window=1):
            raise HTTPException(status_code=400, detail="Invalid TOTP code")

        mfa.is_enabled = True
        await db.commit()
        await log_audit(db=db, action="2fa_enabled", user_id=current_user.id, resource="user_mfa")
        return {"message": "2FA enabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA verify error: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify 2FA")

@app.post("/api/auth/2fa/disable")
async def disable_2fa(password: str = Form(...),
                      current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        if not verify_password(password, current_user.password_hash):
            raise HTTPException(status_code=403, detail="Invalid password")

        result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id))
        mfa = result.scalar_one_or_none()
        if not mfa or not mfa.is_enabled:
            raise HTTPException(status_code=400, detail="2FA not enabled")

        mfa.is_enabled = False
        mfa.totp_secret = ""
        mfa.backup_codes = "[]"
        await db.commit()
        await log_audit(db=db, action="2fa_disabled", user_id=current_user.id, resource="user_mfa")
        return {"message": "2FA disabled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA disable error: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable 2FA")

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
