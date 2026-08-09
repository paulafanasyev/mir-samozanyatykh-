"""
Главный файл FastAPI приложения Мир Самозанятых v7.6
АНО ЦПС ИНН 9724016805
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import logger
from app.core.security import generate_csp_nonce

# Импорт роутеров
from app.api import auth, users, sales, contracts, crm, svetlana, websocket, subscriptions, flutter, email_campaigns, analytics, import_export, search, calendar, notifications, webrtc, ai_analytics, white_label, mfa, telegram_bot, api_keys, webhooks, whatsapp, reports, backups, health, admin, referrals


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup и shutdown"""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    yield
    await close_db()
    logger.info("👋 Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Платформа для самозанятых. АНО ЦПС ИНН 9724016805",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============ MIDDLEWARE ============

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


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Добавление security headers к каждому ответу"""
    nonce = generate_csp_nonce()
    request.state.csp_nonce = nonce
    
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), "
        "payment=(), usb=(), magnetometer=(), gyroscope=()"
    )
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # CSP с nonce
    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://fonts.googleapis.com 'unsafe-inline'; "
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
    """Логирование всех запросов"""
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
                "duration_ms": round(duration, 2),
                "ip_address": request.client.host,
            }
        )
        raise


# ============ ERROR HANDLERS ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Кастомный обработчик HTTP ошибок"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status": exc.status_code,
            "message": exc.detail,
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик непредвиденных ошибок"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status": 500,
            "message": "Внутренняя ошибка сервера" if not settings.DEBUG else str(exc),
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


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
app.include_router(referrals.router)


# ============ HEALTH CHECKS ============

@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    """Корневой endpoint"""
    nonce = request.state.csp_nonce
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{settings.APP_NAME}</title>
    <style nonce="{nonce}">
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #0D47A1 0%, #1976D2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            max-width: 600px;
        }}
        h1 {{ font-size: 3rem; margin-bottom: 16px; font-weight: 700; }}
        p {{ font-size: 1.2rem; opacity: 0.9; margin-bottom: 32px; }}
        .version {{
            display: inline-block;
            background: rgba(255,255,255,0.15);
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9rem;
            backdrop-filter: blur(10px);
        }}
        .links {{
            margin-top: 32px;
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .links a {{
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            transition: all 0.3s;
        }}
        .links a:hover {{
            background: rgba(255,255,255,0.15);
            border-color: rgba(255,255,255,0.5);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Мир Самозанятых</h1>
        <p>Платформа для самозанятых и фрилансеров</p>
        <span class="version">v{settings.APP_VERSION}</span>
        <div class="links">
            <a href="/docs">API Docs</a>
            <a href="/health">Health</a>
        </div>
    </div>
</body>
</html>""")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
