"""
Main FastAPI application - Security Hardened v8.4.1
ANO TsPS INN 9724016805
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import logger
from app.core.security import generate_csp_nonce
from app.core.rate_limit import limiter
from app.core.upload_limit import UploadSizeLimitMiddleware

# Import routers
from app.api import auth, users, sales, contracts, crm, svetlana, websocket
from app.api import subscriptions, flutter, email_campaigns, analytics
from app.api import import_export, search, calendar, notifications, webrtc
from app.api import ai_analytics, white_label, mfa, telegram_bot, api_keys
from app.api import webhooks, whatsapp, reports, backups, health, admin
from app.api import referrals, tasks, export, import_data, accounting, fns, bank, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    yield
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Platform for self-employed. ANO TsPS INN 9724016805",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============ SECURITY MIDDLEWARE ============

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, f"https://{settings.DOMAIN}"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# Trusted Hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[settings.DOMAIN, f"*.{settings.DOMAIN}", "localhost", "127.0.0.1"],
)

# Upload size limit
app.add_middleware(UploadSizeLimitMiddleware)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to every response"""
    nonce = generate_csp_nonce()
    request.state.csp_nonce = nonce

    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), "
        "payment=(), usb=(), magnetometer=(), gyroscope=()"
    )
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    # CSP with nonce
    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        f"font-src 'self' https://fonts.gstatic.com; "
        f"img-src 'self' data: https:; "
        f"connect-src 'self' https://api.openrouter.ai https://api.yookassa.ru; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self';"
    )
    response.headers["Content-Security-Policy"] = csp

    # Timing
    response.headers["X-Response-Time"] = f"{duration:.2f}ms"

    return response


@app.middleware("http")
async def request_logging(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()

    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000

        logger.info(
            f"{request.method} {request.url.path} {response.status_code} "
            f"{duration:.2f}ms {request.client.host}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration, 2),
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent", "")[:100],
            }
        )
        return response

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"{request.method} {request.url.path} ERROR {duration:.2f}ms: {e}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "ip_address": request.client.host,
            }
        )
        raise


# ============ ROUTERS ============

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(sales.router)
app.include_router(contracts.router)
app.include_router(crm.router)
app.include_router(svetlana.router)
app.include_router(websocket.router)
app.include_router(subscriptions.router)
app.include_router(flutter.router)
app.include_router(email_campaigns.router)
app.include_router(analytics.router)
app.include_router(import_export.router)
app.include_router(search.router)
app.include_router(calendar.router)
app.include_router(notifications.router)
app.include_router(webrtc.router)
app.include_router(ai_analytics.router)
app.include_router(white_label.router)
app.include_router(mfa.router)
app.include_router(telegram_bot.router)
app.include_router(api_keys.router)
app.include_router(webhooks.router)
app.include_router(whatsapp.router)
app.include_router(reports.router)
app.include_router(backups.router)
app.include_router(health.router)
app.include_router(admin.router)
app.include_router(referrals.router)
app.include_router(tasks.router)
app.include_router(export.router)
app.include_router(import_data.router)
app.include_router(accounting.router)
app.include_router(fns.router)
app.include_router(bank.router)
app.include_router(metrics.router)


@app.get("/")
@limiter.limit("10/minute")
async def root(request: Request):
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }
