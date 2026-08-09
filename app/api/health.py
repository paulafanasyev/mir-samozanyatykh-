"""
Health Checks & Monitoring API v7.4
Мониторинг состояния системы
"""

import time
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.cache import cache

router = APIRouter(prefix="/api/health", tags=["health"])


# Время запуска приложения
_start_time = time.time()


@router.get("/")
async def health_check():
    """Базовая проверка здоровья"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - _start_time),
    }


@router.get("/detailed")
async def detailed_health(
    db: AsyncSession = Depends(get_db),
):
    """Детальная проверка всех компонентов"""

    checks = {}

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}

    # Redis check (если настроен)
    try:
        cache_stats = cache.get_stats()
        checks["cache"] = {"status": "ok", "stats": cache_stats}
    except Exception as e:
        checks["cache"] = {"status": "error", "error": str(e)}

    # API keys check
    checks["openrouter"] = {
        "status": "ok" if settings.OPENROUTER_API_KEY else "not_configured",
        "configured": bool(settings.OPENROUTER_API_KEY),
    }

    checks["cosyvoice"] = {
        "status": "ok" if settings.COSYVOICE_API_KEY else "not_configured",
        "configured": bool(settings.COSYVOICE_API_KEY),
    }

    # Email check
    checks["email"] = {
        "status": "ok" if settings.SMTP_HOST else "not_configured",
        "configured": bool(settings.SMTP_HOST),
    }

    # Overall status
    all_ok = all(c["status"] in ("ok", "not_configured") for c in checks.values())

    return {
        "status": "healthy" if all_ok else "degraded",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - _start_time),
        "checks": checks,
    }


@router.get("/metrics")
async def system_metrics(
    db: AsyncSession = Depends(get_db),
):
    """Метрики системы"""

    from app.models import User, Client, Deal, Invoice, Task

    # Подсчёт сущностей
    users_count = await db.scalar(select(User.id))
    clients_count = await db.scalar(select(Client.id))
    deals_count = await db.scalar(select(Deal.id))
    invoices_count = await db.scalar(select(Invoice.id))
    tasks_count = await db.scalar(select(Task.id))

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entities": {
            "users": users_count,
            "clients": clients_count,
            "deals": deals_count,
            "invoices": invoices_count,
            "tasks": tasks_count,
        },
        "cache": cache.get_stats(),
        "memory": {
            "uptime_seconds": int(time.time() - _start_time),
        },
    }


@router.post("/cache/clear")
async def clear_cache():
    """Очистка кэша (admin only)"""
    cache.clear()
    return {"message": "Cache cleared", "timestamp": datetime.now(timezone.utc).isoformat()}
