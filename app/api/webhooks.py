"""
Webhooks API - Security Hardened v8.4.2
ANO TsPS INN 9724016805
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.core.logging import logger
from app.services.ssrf import SSRFProtector
from app.services.encryption import token_encryption
from app.models import User, Webhook

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/")
async def create_webhook(
    url: str,
    event_type: str,
    secret: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create webhook with SSRF protection and encrypted secret"""

    # SSRF validation
    is_valid, error = SSRFProtector.validate_webhook_url(url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {error}")

    # Encrypt secret if provided
    encrypted_secret = token_encryption.encrypt(secret) if secret else None

    webhook = Webhook(
        user_id=current_user.id,
        url=url,
        event_type=event_type,
        secret=encrypted_secret,
    )
    db.add(webhook)
    await db.commit()

    return {"status": "created", "id": webhook.id}


@router.get("/")
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List only current user's webhooks"""
    result = await db.execute(
        select(Webhook).where(Webhook.user_id == current_user.id)
    )
    webhooks = result.scalars().all()
    return {"webhooks": [{"id": w.id, "url": w.url, "event": w.event_type} for w in webhooks]}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test webhook - ownership verified"""
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == current_user.id
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {"status": "test_sent", "webhook_id": webhook_id}


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete webhook - ownership verified"""
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == current_user.id
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.commit()

    return {"status": "deleted", "webhook_id": webhook_id}
