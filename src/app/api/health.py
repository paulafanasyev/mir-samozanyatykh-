"""
Health check endpoint for Render.com
MIR Samozanyatykh v8.4 - ANO TsPS INN 9724016805
"""

from datetime import datetime, timezone
import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings


async def _redis_ping():
    import redis.asyncio as redis
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        return await asyncio.wait_for(r.ping(), timeout=2.0)
    finally:
        await r.aclose()

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
        checks["database"] = "error"
        checks["status"] = "degraded"

    # Redis check
    try:
        await _redis_ping()
        checks["redis"] = "connected"
    except Exception as e:
        checks["redis"] = f"error: {type(e).__name__}"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "healthy" else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(content=checks, status_code=status_code)


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe: only ready when DB and Redis are reachable."""
    checks = {"database": False, "redis": False}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        checks["redis"] = bool(await _redis_ping())
    except Exception:
        pass
    ready = all(checks.values())
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={"ready": ready, "checks": checks, "timestamp": datetime.now(timezone.utc).isoformat()},
        status_code=200 if ready else 503,
    )


@router.get("/live")
async def liveness_check():
    """Liveness probe (fast, no DB)"""
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
