"""
Логирование приложения Мир Самозанятых v7.5
"""

import logging
import sys
import json
import re
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .config import settings


SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,]+"),
    re.compile(r"(?i)(password\s*[=:]\s*)[^\s,]+"),
    re.compile(r"(?i)(token\s*[=:]\s*)[^\s,]+"),
    re.compile(r"(?i)(secret\s*[=:]\s*)[^\s,]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s,]+"),
]

def redact(value: str) -> str:
    for pattern in SENSITIVE_PATTERNS:
        value = pattern.sub(r"\1[REDACTED]", value)
    return value


class JSONFormatter(logging.Formatter):
    """JSON форматтер для структурированных логов"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Добавляем extra поля
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
            
        if record.exc_info:
            log_data["exception"] = redact(self.formatException(record.exc_info))
            
        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging() -> logging.Logger:
    """Настройка логирования приложения"""
    
    logger = logging.getLogger("mir-samozanyatykh")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Очищаем старые хендлеры
    logger.handlers = []
    
    # Форматтер для консоли (человекочитаемый)
    console_formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Форматтер для файла (JSON)
    json_formatter = JSONFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    logger.addHandler(console_handler)
    
    # Rotating file handlers prevent unbounded disk growth.
    file_handler = RotatingFileHandler(settings.LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # Error file handler (только ERROR+)
    error_file = Path(settings.LOG_FILE).parent / "error.log"
    error_handler = RotatingFileHandler(str(error_file), maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
    
    return logger


# Глобальный логгер
logger = setup_logging()


def log_audit(
    action: str,
    user_id: int = None,
    ip_address: str = None,
    details: str = None,
    success: bool = True,
    **kwargs
) -> None:
    """Запись аудит-лога"""
    extra = {
        "user_id": user_id,
        "ip_address": ip_address,
        "action": action,
    }
    msg = f"AUDIT: {action} | user={user_id} | success={success}"
    if details:
        msg += f" | {details}"
    logger.info(msg, extra=extra)
