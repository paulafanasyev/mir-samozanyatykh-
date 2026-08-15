from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import platform

from app.core.database import get_db

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("", summary="Healthcheck")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "version": "8.6.1",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production",
    }

@router.get("/ready", summary="Readiness probe")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Проверка готовности к трафику (проверяет БД)"""
    try:
        await db.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": str(e)}

@router.get("/live", summary="Liveness probe")
async def liveness_check():
    """Проверка что сервис жив"""
    return {"status": "alive"}

@router.get("/metrics", summary="System metrics")
async def system_metrics():
    """Системные метрики для мониторинга"""
    import psutil
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total": psutil.disk_usage("/").total,
            "free": psutil.disk_usage("/").free,
            "percent": psutil.disk_usage("/").percent,
        },
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }
