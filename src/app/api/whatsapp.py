"""
WhatsApp Business API v7.3
Интеграция WhatsApp для уведомлений и общения с клиентами
"""

import os
import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import log_audit
from app.core.auth import get_current_user, get_current_user_optional
from app.core.rate_limit import rate_limit
from app.models import User, Client

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


class WhatsAppConnect(BaseModel):
    phone_number: str
    business_name: Optional[str] = None


class WhatsAppMessage(BaseModel):
    client_id: Optional[int] = None
    phone: Optional[str] = None
    message: str
    template_name: Optional[str] = None  # для шаблонов WhatsApp


# ============ USER CONNECTION ============

@router.post("/connect")
async def connect_whatsapp(
    data: WhatsAppConnect,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Привязка WhatsApp Business аккаунта"""
    current_user.whatsapp_phone = data.phone_number
    current_user.whatsapp_business_name = data.business_name
    await db.commit()

    await log_audit(
        action="whatsapp_connected",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Phone: {data.phone_number}",
    )
    return {
        "message": "WhatsApp Business подключен",
        "phone": data.phone_number,
    }


@router.delete("/disconnect")
async def disconnect_whatsapp(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отвязка WhatsApp"""
    current_user.whatsapp_phone = None
    current_user.whatsapp_business_name = None
    await db.commit()

    await log_audit(
        action="whatsapp_disconnected",
        user_id=current_user.id,
        ip_address=request.client.host,
    )
    return {"message": "WhatsApp отключен"}


@router.get("/status")
async def whatsapp_status(
    current_user: User = Depends(get_current_user),
):
    """Статус подключения WhatsApp"""
    return {
        "connected": bool(current_user.whatsapp_phone),
        "phone": current_user.whatsapp_phone,
        "business_name": current_user.whatsapp_business_name,
    }


# ============ SEND MESSAGES ============

async def send_whatsapp_message(phone: str, message: str, template: str = None):
    """Отправка сообщения через WhatsApp Business API"""
    import aiohttp

    api_token = os.getenv("WHATSAPP_API_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")

    if not api_token or not phone_id:
        return False

    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    # Если шаблон — отправляем через template
    if template:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "template",
            "template": {"name": template, "language": {"code": "ru"}},
        }
    else:
        # Обычное текстовое сообщение
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {"body": message, "preview_url": False},
        }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                return resp.status == 200
    except Exception as e:
        import logging
        logging.error(f"WhatsApp send error: {e}")
        return False


@router.post("/send")
@rate_limit("20/minute")
async def send_message(
    data: WhatsAppMessage,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отправка сообщения через WhatsApp"""
    if not current_user.whatsapp_phone:
        raise HTTPException(status_code=400, detail="WhatsApp не подключен")

    # Определяем получателя
    phone = data.phone
    if data.client_id:
        result = await db.execute(
            select(Client).where(
                Client.id == data.client_id,
                Client.user_id == current_user.id,
            )
        )
        client = result.scalar_one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        if client.phone:
            phone = client.phone
        elif not phone:
            raise HTTPException(status_code=400, detail="У клиента нет номера телефона")

    if not phone:
        raise HTTPException(status_code=400, detail="Не указан номер телефона")

    # Форматируем номер
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")

    if len(data.message.strip()) == 0 or len(data.message) > 4096:
        raise HTTPException(status_code=422, detail="Сообщение должно содержать от 1 до 4096 символов")

    background_tasks.add_task(
        send_whatsapp_message,
        phone,
        data.message,
        data.template_name,
    )

    await log_audit(
        action="whatsapp_message_queued",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"To: {phone[:6]}...",
    )

    return {"message": "Сообщение поставлено в очередь", "recipient": phone[:6] + "..."}


# ============ TEMPLATES ============

@router.get("/templates")
async def list_templates(
    current_user: User = Depends(get_current_user),
):
    """Список шаблонов WhatsApp"""
    return {
        "templates": [
            {
                "name": "appointment_reminder",
                "description": "Напоминание о встрече",
                "category": "UTILITY",
            },
            {
                "name": "invoice_notification",
                "description": "Уведомление о счёте",
                "category": "UTILITY",
            },
            {
                "name": "payment_received",
                "description": "Подтверждение оплаты",
                "category": "UTILITY",
            },
            {
                "name": "welcome_message",
                "description": "Приветственное сообщение",
                "category": "MARKETING",
            },
        ]
    }


# ============ WEBHOOK ============

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Webhook для входящих сообщений от WhatsApp"""
    body = await request.body()
    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not app_secret:
        raise HTTPException(status_code=503, detail="WhatsApp webhook is not configured")
    if not signature.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid WhatsApp webhook signature")
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature[7:], expected):
        raise HTTPException(status_code=401, detail="Invalid WhatsApp webhook signature")

    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Invalid webhook JSON")

    entry = data.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})

    messages = value.get("messages", [])
    for msg in messages:
        from_phone = msg.get("from")
        text = msg.get("text", {}).get("body", "")

        # Найти клиента по номеру только после проверки подписи.
        normalized_phone = from_phone.replace("+", "").replace(" ", "").replace("-", "") if from_phone else ""
        result = await db.execute(select(Client).where(Client.phone == from_phone))
        clients = result.scalars().all()

        # Один номер может существовать у разных пользователей. Не допускаем
        # cross-tenant запись при неоднозначном совпадении.
        client = clients[0] if len(clients) == 1 else None

        if client:
            from app.models import Call
            call = Call(
                user_id=client.user_id,
                client_id=client.id,
                direction="in",
                notes=f"WhatsApp: {text}",
            )
            db.add(call)
            await db.commit()

    return {"status": "received"}


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    """Верификация webhook от Meta"""
    verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
    if not verify_token:
        raise ValueError('WHATSAPP_VERIFY_TOKEN must be set')

    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge)

    raise HTTPException(status_code=403, detail="Verification failed")
