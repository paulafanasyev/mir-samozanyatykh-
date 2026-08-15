"""
Webhooks API for Mir Samozanyatykh v8.2
Real creation, signature verification, replay protection
"""

import hmac
import hashlib
import secrets
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User, Webhook, WebhookDelivery
from app.services.ssrf import validate_url, safe_request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def generate_webhook_secret() -> str:
    """Cryptographically secure random secret"""
    return secrets.token_urlsafe(32)


def verify_webhook_signature(payload: bytes, signature: str, secret: str, timestamp: str) -> bool:
    """Verify webhook signature with 5-minute window"""
    try:
        ts = int(timestamp)
        now = int(time.time())
        if abs(now - ts) > 300:
            return False
    except ValueError:
        return False

    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.{payload.decode()}".encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@router.post("")
async def create_webhook(
    url: str,
    events: list,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create real webhook with secure secret"""
    if not validate_url(url):
        raise HTTPException(400, "Invalid URL")

    secret = generate_webhook_secret()
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()

    webhook = Webhook(
        user_id=current_user.id,
        url=url,
        events=events,
        secret=secret,
        secret_hash=secret_hash,
        is_active=True
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    return {
        "id": webhook.id,
        "url": webhook.url,
        "events": webhook.events,
        "secret": secret,
        "created_at": webhook.created_at
    }


@router.get("")
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's webhooks (without secrets)"""
    webhooks = db.query(Webhook).filter(Webhook.user_id == current_user.id).all()

    return [{
        "id": w.id,
        "url": w.url,
        "events": w.events,
        "is_active": w.is_active,
        "created_at": w.created_at
    } for w in webhooks]


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete webhook with ownership check"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user.id
    ).first()

    if not webhook:
        raise HTTPException(404, "Webhook not found")

    db.delete(webhook)
    db.commit()
    return {"message": "Deleted"}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test webhook with ownership check BEFORE network request"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user.id
    ).first()

    if not webhook:
        raise HTTPException(404, "Webhook not found")

    try:
        payload = b'{"test": true}'
        response = safe_request(
            webhook.url,
            method="POST",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/incoming/{webhook_id}")
async def receive_webhook(
    webhook_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Receive incoming webhook with signature verification"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.is_active == True
    ).first()

    if not webhook:
        raise HTTPException(404, "Webhook not found")

    signature = request.headers.get("X-Webhook-Signature")
    timestamp = request.headers.get("X-Webhook-Timestamp")

    if not signature or not timestamp:
        raise HTTPException(401, "Missing signature")

    body = await request.body()
    if not verify_webhook_signature(body, signature, webhook.secret, timestamp):
        raise HTTPException(401, "Invalid signature")

    event_id = request.headers.get("X-Event-ID")
    if event_id:
        existing = db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id,
            WebhookDelivery.event == event_id
        ).first()
        if existing:
            raise HTTPException(409, "Duplicate event")

    delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event=event_id or "unknown",
        payload=body.decode(),
        success=True
    )
    db.add(delivery)
    db.commit()

    return {"status": "processed"}
