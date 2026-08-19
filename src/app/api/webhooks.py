"""
Webhooks API - Security Hardened v8.4.3
ANO TsPS INN 9724016805
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
import hashlib, hmac, time, json, secrets
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.config import settings
from app.core.logging import logger
from app.core.auth import get_current_user, get_current_user_optional
from app.services.ssrf import SSRFProtector
from app.services.encryption import get_token_encryption
from app.core.rate_limit import limiter
from app.models import User, Webhook, WebhookDelivery

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

class WebhookCreate(BaseModel):
    url: str = Field(..., min_length=8, max_length=500)
    events: List[str] = Field(default_factory=list, max_length=20)
    secret: Optional[str] = Field(None, min_length=16, max_length=255)



@router.post("/")
@limiter.limit("10/minute")
async def create_webhook(
    webhook_in: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create webhook with SSRF protection and encrypted secret."""
    is_valid, error = SSRFProtector.validate_webhook_url(webhook_in.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {error}")
    generated_secret = not webhook_in.secret
    secret = webhook_in.secret or secrets.token_urlsafe(32)
    encrypted_secret = get_token_encryption().encrypt(secret)
    webhook = Webhook(
        user_id=current_user.id,
        url=webhook_in.url,
        events=webhook_in.events,
        secret=encrypted_secret,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    result = {"status": "created", "id": webhook.id}
    if generated_secret:
        result["secret"] = secret
    return result


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
    return {"webhooks": [{"id": w.id, "url": w.url, "events": w.events or [], "is_active": w.is_active, "failure_count": w.failure_count, "last_delivered_at": w.last_delivered_at, "last_error": w.last_error, "created_at": w.created_at} for w in webhooks]}


@router.post("/{webhook_id}/test")
@limiter.limit("5/minute")
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

    is_valid, validation_error = SSRFProtector.validate_webhook_url(webhook.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {validation_error}")
    timestamp=str(int(time.time()))
    payload={"event":"test","webhook_id":webhook.id,"timestamp":timestamp}
    body=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    headers={"Content-Type":"application/json","X-Webhook-Timestamp":timestamp}
    if webhook.secret:
        secret=get_token_encryption().decrypt(webhook.secret)
        headers["X-Webhook-Signature"]=hmac.new(secret.encode(), f"{timestamp}.".encode()+body, hashlib.sha256).hexdigest()
    started = time.perf_counter()
    delivery = WebhookDelivery(webhook_id=webhook.id, event="test", payload=payload)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0,connect=3.0),follow_redirects=False) as client:
            resp=await client.post(webhook.url,content=body,headers=headers)
        delivery.response_status = resp.status_code
        delivery.response_body = resp.text[:4000]
        delivery.success = 200 <= resp.status_code < 300
        delivery.duration_ms = int((time.perf_counter() - started) * 1000)
        webhook.last_delivered_at = datetime.now(timezone.utc) if delivery.success else webhook.last_delivered_at
        webhook.failure_count = 0 if delivery.success else webhook.failure_count + 1
        db.add(delivery)
        await db.commit()
        return {"status":"test_sent","webhook_id":webhook_id,"http_status":resp.status_code,"success":delivery.success}
    except httpx.HTTPError:
        delivery.success = False
        delivery.duration_ms = int((time.perf_counter() - started) * 1000)
        webhook.failure_count += 1
        webhook.last_error = "Webhook delivery failed"
        db.add(delivery)
        await db.commit()
        raise HTTPException(status_code=502,detail="Webhook delivery failed")


@router.get("/{webhook_id}/deliveries")
async def list_webhook_deliveries(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == current_user.id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.webhook_id == webhook_id).order_by(WebhookDelivery.created_at.desc()).limit(100)
    )
    deliveries = result.scalars().all()
    return [{
        "id": d.id, "event": d.event, "response_status": d.response_status,
        "success": d.success, "duration_ms": d.duration_ms, "created_at": d.created_at,
    } for d in deliveries]


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
