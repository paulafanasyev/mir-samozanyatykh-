"""
API вебхуков v7.9
Подписка, доставка, retry логика, HMAC подпись
АНО ЦПС ИНН 9724016805
"""

import secrets
import hmac
import hashlib
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import logger, log_audit
from app.models import User, Webhook, WebhookDelivery

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# ============ SCHEMAS ============

class WebhookCreate(BaseModel):
    url: str = Field(..., max_length=500)
    events: List[str] = Field(default=["invoice.paid", "deal.won"])


class WebhookOut(BaseModel):
    id: int
    url: str
    events: List[str]
    is_active: bool
    failure_count: int
    last_delivered_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookUpdate(BaseModel):
    url: Optional[str] = Field(None, max_length=500)
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


class DeliveryOut(BaseModel):
    id: int
    event: str
    payload: dict
    response_status: Optional[int]
    success: bool
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ HELPERS ============

def generate_webhook_secret() -> str:
    """Генерация секрета для HMAC подписи"""
    return secrets.token_hex(32)


def sign_payload(payload: dict, secret: str) -> str:
    """HMAC-SHA256 подпись payload"""
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


async def deliver_webhook(webhook: Webhook, event: str, payload: dict):
    """Доставка вебхука с retry логикой"""
    import httpx

    full_payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }
    signature = sign_payload(full_payload, webhook.secret)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": event,
        "X-Webhook-ID": str(webhook.id),
        "User-Agent": "MirSamozanyatykh-Webhook/1.0",
    }

    start_time = datetime.now(timezone.utc)
    success = False
    response_status = None
    response_body = None
    duration_ms = None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook.url, json=full_payload, headers=headers)
            response_status = response.status_code
            response_body = response.text[:2000]
            success = 200 <= response.status_code < 300
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
    except Exception as e:
        response_body = str(e)[:2000]
        logger.error(f"Webhook delivery failed: {e}")

    return success, response_status, response_body, duration_ms


# ============ ENDPOINTS ============

@router.post("/", response_model=WebhookOut, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание вебхука"""
    # Лимит вебхуков
    count = await db.scalar(
        select(func.count(Webhook.id)).where(
            Webhook.user_id == current_user.id,
            Webhook.is_active == True,
        )
    )
    if count >= 20:
        raise HTTPException(status_code=400, detail="Максимум 20 активных вебхуков")

    webhook = Webhook(
        user_id=current_user.id,
        url=data.url,
        events=data.events,
        secret=generate_webhook_secret(),
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    await log_audit(
        action="webhook_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Webhook {webhook.id} for {data.url}",
    )
    return WebhookOut.model_validate(webhook)


@router.get("/", response_model=List[WebhookOut])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список вебхуков пользователя"""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.user_id == current_user.id)
        .order_by(Webhook.created_at.desc())
    )
    webhooks = result.scalars().all()
    return [WebhookOut.model_validate(w) for w in webhooks]


@router.put("/{webhook_id}", response_model=WebhookOut)
async def update_webhook(
    webhook_id: int,
    update: WebhookUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновление вебхука"""
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Вебхук не найден")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(webhook, key, value)

    await db.commit()
    await db.refresh(webhook)

    await log_audit(
        action="webhook_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Webhook {webhook_id} updated",
    )
    return WebhookOut.model_validate(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление вебхука"""
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Вебхук не найден")

    await db.delete(webhook)
    await db.commit()

    await log_audit(
        action="webhook_deleted",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Webhook {webhook_id} deleted",
    )


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Тестовая отправка вебхука"""
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Вебхук не найден")

    test_payload = {
        "test": True,
        "message": "Это тестовое событие от Мир Самозанятых",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    success, status_code, body, duration = await deliver_webhook(
        webhook, "test", test_payload
    )

    # Сохранить доставку
    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event="test",
        payload=test_payload,
        response_status=status_code,
        response_body=body,
        success=success,
        duration_ms=duration,
    )
    db.add(delivery)

    if success:
        webhook.last_delivered_at = datetime.now(timezone.utc)
        webhook.failure_count = 0
        webhook.last_error = None
    else:
        webhook.failure_count += 1
        webhook.last_error = body
        if webhook.failure_count >= 10:
            webhook.is_active = False

    await db.commit()

    return {
        "success": success,
        "status_code": status_code,
        "duration_ms": duration,
        "response_preview": body[:200] if body else None,
    }


@router.get("/{webhook_id}/deliveries", response_model=List[DeliveryOut])
async def list_deliveries(
    webhook_id: int,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """История доставок вебхука"""
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Вебхук не найден")

    deliveries_result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(desc(WebhookDelivery.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    deliveries = deliveries_result.scalars().all()
    return [DeliveryOut.model_validate(d) for d in deliveries]


# ============ SERVICE FUNCTION ============

async def trigger_webhooks(
    db: AsyncSession,
    user_id: int,
    event: str,
    payload: dict,
):
    """Триггер всех вебхуков пользователя для события"""
    result = await db.execute(
        select(Webhook).where(
            Webhook.user_id == user_id,
            Webhook.is_active == True,
        )
    )
    webhooks = result.scalars().all()

    for webhook in webhooks:
        if event not in webhook.events:
            continue

        success, status_code, body, duration = await deliver_webhook(webhook, event, payload)

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event=event,
            payload=payload,
            response_status=status_code,
            response_body=body,
            success=success,
            duration_ms=duration,
        )
        db.add(delivery)

        if success:
            webhook.last_delivered_at = datetime.now(timezone.utc)
            webhook.failure_count = 0
            webhook.last_error = None
        else:
            webhook.failure_count += 1
            webhook.last_error = body
            if webhook.failure_count >= 10:
                webhook.is_active = False

    await db.commit()
