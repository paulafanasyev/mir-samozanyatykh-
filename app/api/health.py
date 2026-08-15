"""
Health check endpoint for Render.com
MIR Samozanyatykh v8.4 - ANO TsPS INN 9724016805
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Full system health check"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }

    # DB check
    try:
        result = await db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        checks["status"] = "degraded"

    # Redis check
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        checks["redis"] = "connected"
        await r.close()
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    status_code = 200 if checks["status"] == "healthy" else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(content=checks, status_code=status_code)


@router.get("/ready")
async def readiness_check():
    """Readiness probe for Render/K8s"""
    return {
        "ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/live")
async def liveness_check():
    """Liveness probe (fast, no DB)"""
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
