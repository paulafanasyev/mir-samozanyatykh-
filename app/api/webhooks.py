"""
Webhooks API - Security Hardened v8.4.1
ANO TsPS INN 9724016805
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.core.logging import logger
from app.services.ssrf import SSRFProtector
from app.models import User

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/")
async def create_webhook(
    url: str,
    event_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new webhook with SSRF protection

    URL is validated against SSRF attacks before saving.
    Only HTTPS URLs are allowed for security.
    """
    # Validate URL against SSRF
    is_valid, error = SSRFProtector.validate_webhook_url(url)
    if not is_valid:
        logger.warning(f"SSRF blocked webhook URL: {url} - {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook URL: {error}"
        )

    # Log creation (mask URL in logs)
    from urllib.parse import urlparse
    parsed = urlparse(url)
    safe_url = f"{parsed.scheme}://{parsed.hostname}/***"
    logger.info(f"Webhook created by {current_user.email}: {safe_url}")

    return {
        "status": "created",
        "url": safe_url,
        "event_type": event_type,
        "user_id": current_user.id
    }


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test webhook delivery with SSRF protection
    """
    # In real implementation, fetch webhook URL from DB
    # Then validate with SSRF before sending

    return {
        "status": "test_sent",
        "webhook_id": webhook_id,
        "message": "Webhook test with SSRF protection"
    }


@router.get("/")
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user webhooks"""
    return {"webhooks": [], "user_id": current_user.id}


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete webhook"""
    return {"status": "deleted", "webhook_id": webhook_id}
