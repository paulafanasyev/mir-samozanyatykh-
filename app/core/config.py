"""
Конфигурация приложения Мир Самозанятых v8.0
АНО ЦПС ИНН 9724016805
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Настройки приложения с валидацией"""
    
    # Основные
    APP_NAME: str = "Мир Самозанятых"
    APP_VERSION: str = "8.4.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Безопасность
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_WINDOW: int = 60
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30
    
    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://mir_user:change_me@localhost:5432/mir_samozanyatykh"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_DB_SESSION: int = 1
    REDIS_DB_CACHE: int = 2
    REDIS_DB_RATE_LIMIT: int = 3
    
    # Email (SMTP SSL)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "Мир Самозанятых"
    SMTP_TLS: bool = True
    
    # Домен
    DOMAIN: str = "localhost:8000"
    FRONTEND_URL: str = "https://localhost:3000"
    
    # Загрузка файлов
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_EXTENSIONS: str = "jpg,jpeg,png,pdf,doc,docx"
    UPLOAD_DIR: str = "data/uploads"
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    
    # AI / OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL_DEFAULT: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_MODEL_CHEAP: str = "openai/gpt-4o-mini"
    
    # CosyVoice 3.0 (голосовой ассистент)
    COSYVOICE_API_KEY: str = ""
    COSYVOICE_API_URL: str = "https://api.openrouter.ai/v1/audio/speech"
    COSYVOICE_MODEL: str = "cosyvoice-v1"
    COSYVOICE_VOICE: str = "svetlana"
    
    # ФНС
    FNS_API_URL: str = "https://api-fns.ru/api/"
    FNS_API_KEY: str = ""
    
    # Банки
    TINKOFF_API_TOKEN: str = ""
    SBER_API_TOKEN: str = ""
    VTB_API_TOKEN: str = ""
    
    # ЮKassa
    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_SECRET_KEY: str = ""
    YOOKASSA_RETURN_URL: str = "https://{domain}/payment/success"
    YOOKASSA_CANCEL_URL: str = "https://{domain}/payment/cancel"
    
    # SMS.ru
    SMS_RU_API_KEY: str = ""
    SMS_RU_SENDER: str = "MirSamoz"
    
    # OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    YANDEX_CLIENT_ID: str = ""
    YANDEX_CLIENT_SECRET: str = ""
    TELEGRAM_OAUTH_BOT: str = ""
    
    # Telegram бот
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    
    # КриптоПро (опционально)
    CRYPTOPRO_ENABLED: bool = False
    
    # WebRTC
    WEBRTC_STUN_SERVER: str = "stun:stun.l.google.com:19302"
    WEBRTC_TURN_SERVER: str = ""
    WEBRTC_TURN_USER: str = ""
    WEBRTC_TURN_PASS: str = ""
    
    # Подписки
    SUBSCRIPTION_TIERS: dict = {
        "free": {"price": 0, "features": ["base"]},
        "pro": {"price": 499, "features": ["base", "contracts", "ai"]},
        "business": {"price": 1499, "features": ["base", "contracts", "ai", "yookassa", "priority"]},
        "enterprise": {"price": 4999, "features": ["all"]},
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Валидация SECRET_KEY в production
if settings.ENVIRONMENT == "production":
    if len(settings.SECRET_KEY) < 32:
        raise ValueError(
            "SECRET_KEY must be at least 32 chars in production.\n"
            "Generate: openssl rand -hex 64"
        )
    if settings.SECRET_KEY == "change-me-in-production":
        raise ValueError("Change default SECRET_KEY before deploying to production!")

# Создание директорий
Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
