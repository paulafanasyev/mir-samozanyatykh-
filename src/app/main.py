"""
Main FastAPI application - Security Hardened v8.4.3
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
from app.api.metrics import record_request

# Import routers
from app.api import auth, users, sales, contracts, crm, svetlana, websocket
from app.api import subscriptions, flutter, email_campaigns, analytics
from app.api import import_export, search, calendar, notifications, webrtc
from app.api import ai_analytics, white_label, mfa, telegram_bot, api_keys
from app.api import webhooks, whatsapp, reports, backups, health, admin
from app.api import referrals, tasks, export, import_data, accounting, fns, bank, metrics
from app.html_routes import router as html_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    if settings.ENVIRONMENT == "production":
        if len(settings.SECRET_KEY) < 32:
            raise RuntimeError("SECRET_KEY must be at least 32 characters in production")
        if not settings.BANK_ENCRYPTION_KEY:
            raise RuntimeError("BANK_ENCRYPTION_KEY is required in production")
    # Production schema is managed exclusively by Alembic in startup.sh.
    # create_all remains available for local development/tests only.
    if settings.ENVIRONMENT != "production":
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
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Client-Type", "Idempotency-Key", "Accept"],
    max_age=600,
)

# Trusted Hosts
# Localhost is permitted only outside production; production must accept
# requests addressed to the configured public domain only.
_allowed_hosts = [settings.DOMAIN, f"*.{settings.DOMAIN}"]
if settings.ENVIRONMENT != "production":
    _allowed_hosts.extend(["localhost", "127.0.0.1"])
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=_allowed_hosts,
)

# Upload size limit
app.add_middleware(UploadSizeLimitMiddleware)


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path == "/api/auth/refresh":
        # Browser refresh uses a cookie and therefore requires double-submit CSRF.
        # Native mobile clients send the refresh token in the request body and do not use the browser cookie.
        if request.headers.get("X-Client-Type", "").lower() not in {"mobile", "flutter"}:
            import hmac
            csrf_cookie = request.cookies.get("csrf_token")
            csrf_header = request.headers.get("X-CSRF-Token")
            if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
                return JSONResponse(status_code=403, content={"detail": "CSRF token required"})
    return await call_next(request)


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
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    # CSP with nonce
    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self' 'nonce-{nonce}'; "
        f"font-src 'self'; "
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
        record_request(response.status_code, duration / 1000.0)

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
            f"{request.method} {request.url.path} ERROR {duration:.2f}ms",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error_type": type(e).__name__,
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
app.include_router(html_router)


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
