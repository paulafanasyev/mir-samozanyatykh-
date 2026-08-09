"""
Webhooks API v7.1
Исходящие webhooks для интеграций
"""

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# Хранилище вебхуков (в проде — в БД)
_webhooks: dict = {}


class WebhookCreate(BaseModel):
    name: str
    url: str
    events: List[str]  # deal.created, deal.updated, invoice.paid, etc.
    secret: Optional[str] = None
    is_active: bool = True


class WebhookOut(BaseModel):
    id: str
    name: str
    url: str
    events: List[str]
    is_active: bool
    last_triggered_at: Optional[datetime]
    created_at: datetime


# ============ CRUD ============

@router.get("/")
async def list_webhooks(
    current_user: User = Depends(get_current_user),
):
    """Список вебхуков"""
    user_hooks = _webhooks.get(current_user.id, {})
    return {
        "webhooks": [
            {
                "id": h["id"],
                "name": h["name"],
                "url": h["url"],
                "events": h["events"],
                "is_active": h["is_active"],
                "last_triggered_at": h.get("last_triggered_at"),
                "created_at": h["created_at"],
            }
            for h in user_hooks.values()
        ]
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_webhook(
    hook: WebhookCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Создание вебхука"""
    import secrets

    user_hooks = _webhooks.get(current_user.id, {})
    if len(user_hooks) >= 20:
        raise HTTPException(status_code=403, detail="Максимум 20 вебхуков")

    hook_id = secrets.token_urlsafe(16)

    hook_record = {
        "id": hook_id,
        "name": hook.name,
        "url": hook.url,
        "events": hook.events,
        "secret": hook.secret or secrets.token_urlsafe(32),
        "is_active": hook.is_active,
        "last_triggered_at": None,
        "created_at": datetime.now(timezone.utc),
    }

    if current_user.id not in _webhooks:
        _webhooks[current_user.id] = {}
    _webhooks[current_user.id][hook_id] = hook_record

    await log_audit(
        action="webhook_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Webhook: {hook.name}, events: {', '.join(hook.events)}",
    )

    return {
        "message": "Вебхук создан",
        "webhook_id": hook_id,
        "secret": hook_record["secret"],  # Показываем только при создании
    }


@router.put("/{hook_id}")
async def update_webhook(
    hook_id: str,
    hook: WebhookCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Обновление вебхука"""
    user_hooks = _webhooks.get(current_user.id, {})
    if hook_id not in user_hooks:
        raise HTTPException(status_code=404, detail="Вебхук не найден")

    user_hooks[hook_id].update({
        "name": hook.name,
        "url": hook.url,
        "events": hook.events,
        "is_active": hook.is_active,
    })

    await log_audit(
        action="webhook_updated",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Webhook: {hook_id}",
    )

    return {"message": "Вебхук обновлён"}


@router.delete("/{hook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    hook_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Удаление вебхука"""
    user_hooks = _webhooks.get(current_user.id, {})
    if hook_id not in user_hooks:
        raise HTTPException(status_code=404, detail="Вебхук не найден")

    del user_hooks[hook_id]

    await log_audit(
        action="webhook_deleted",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Webhook: {hook_id}",
    )


# ============ TRIGGER ============

async def trigger_webhooks(
    user_id: int,
    event: str,
    payload: dict,
    background_tasks: BackgroundTasks = None,
):
    """Триггер вебхуков по событию"""
    import aiohttp

    user_hooks = _webhooks.get(user_id, {})

    for hook in user_hooks.values():
        if not hook["is_active"]:
            continue
        if event not in hook["events"] and "*" not in hook["events"]:
            continue

        # Подготовка payload
        webhook_payload = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }

        # Подпись
        secret = hook.get("secret", "")
        signature = hmac.new(
            secret.encode(),
            json.dumps(webhook_payload, default=str).encode(),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event,
        }

        # Отправка
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    hook["url"],
                    json=webhook_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    hook["last_triggered_at"] = datetime.now(timezone.utc)
                    hook["last_status"] = resp.status
        except Exception:
            hook["last_triggered_at"] = datetime.now(timezone.utc)
            hook["last_status"] = 0


# ============ EVENTS ============

@router.get("/events")
async def list_events():
    """Список доступных событий для вебхуков"""
    return {
        "events": [
            {"name": "deal.created", "description": "Создание сделки"},
            {"name": "deal.updated", "description": "Обновление сделки"},
            {"name": "deal.won", "description": "Сделка выиграна"},
            {"name": "deal.lost", "description": "Сделка проиграна"},
            {"name": "invoice.created", "description": "Создание счёта"},
            {"name": "invoice.paid", "description": "Оплата счёта"},
            {"name": "client.created", "description": "Новый клиент"},
            {"name": "task.completed", "description": "Задача выполнена"},
            {"name": "call.ended", "description": "Звонок завершён"},
            {"name": "*", "description": "Все события"},
        ]
    }
