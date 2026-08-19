"""
Upload size limit middleware - Security Hardened v8.4.3
ANO TsPS INN 9724016805
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger


class UploadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce upload size limits"""

    async def dispatch(self, request: Request, call_next):
        # Enforce body size for every request; endpoint-level checks enforce file semantics.
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

                if size > max_size:
                    logger.warning(f"Upload rejected: {size} bytes exceeds limit of {max_size} bytes")
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
            except ValueError:
                pass

        response = await call_next(request)
        return response
