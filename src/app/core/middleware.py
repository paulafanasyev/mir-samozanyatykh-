import time
import logging
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.requests")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request metadata without exception bodies, query strings or credentials."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        client = request.client.host if request.client else "unknown"
        logger.info("request_started", extra={"request_id": request_id, "method": request.method, "path": request.url.path, "client": client})
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            logger.info("request_finished", extra={"request_id": request_id, "method": request.method, "path": request.url.path, "status": response.status_code, "duration_ms": round(duration * 1000, 2)})
            return response
        except Exception:
            duration = time.time() - start_time
            logger.exception("request_failed", extra={"request_id": request_id, "method": request.method, "path": request.url.path, "duration_ms": round(duration * 1000, 2)})
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security response headers."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
