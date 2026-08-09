"""
Telegram Bot API v7.1
Бот для уведомлений и управления через Telegram
"""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User, Client, Deal, Task

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


class TelegramConnect(BaseModel):
    telegram_id: str
    username: Optional[str] = None


class TelegramMessage(BaseModel):
    message: str
    client_id: Optional[int] = None


# ============ USER CONNECTION ============

@router.post("/connect")
async def connect_telegram(
    data: TelegramConnect,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Привязка Telegram аккаунта"""
    current_user.telegram_id = data.telegram_id
    current_user.telegram_username = data.username
    await db.commit()

    await log_audit(
        action="telegram_connected",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Telegram ID: {data.telegram_id}",
    )
    return {"message": "Telegram подключен", "telegram_id": data.telegram_id}


@router.delete("/disconnect")
async def disconnect_telegram(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отвязка Telegram"""
    current_user.telegram_id = None
    current_user.telegram_username = None
    await db.commit()

    await log_audit(
        action="telegram_disconnected",
        user_id=current_user.id,
        ip_address=request.client.host,
    )
    return {"message": "Telegram отключен"}


@router.get("/status")
async def telegram_status(
    current_user: User = Depends(get_current_user),
):
    """Статус подключения Telegram"""
    return {
        "connected": bool(current_user.telegram_id),
        "telegram_id": current_user.telegram_id,
        "username": current_user.telegram_username,
    }


# ============ SEND MESSAGES ============

async def send_telegram_message(telegram_id: str, message: str):
    """Отправка сообщения через Telegram Bot API"""
    import aiohttp

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token or not telegram_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return resp.status == 200
    except Exception as e:
        import logging
        logging.error(f"Telegram send error: {e}")
        return False


@router.post("/send")
async def send_message(
    data: TelegramMessage,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отправка сообщения через Telegram"""
    if not current_user.telegram_id:
        raise HTTPException(status_code=400, detail="Telegram не подключен")

    message = f"📢 <b>{current_user.full_name or 'Мир Самозанятых'}</b>\n\n{data.message}"

    background_tasks.add_task(
        send_telegram_message,
        current_user.telegram_id,
        message,
    )

    await log_audit(
        action="telegram_message_sent",
        user_id=current_user.id,
        ip_address=request.client.host,
    )
    return {"message": "Сообщение отправлено"}


# ============ NOTIFICATIONS ============

async def notify_deal_update_telegram(user: User, deal: Deal):
    """Уведомление об изменении сделки в Telegram"""
    if not user.telegram_id:
        return

    message = f"""
📊 <b>Сделка обновлена</b>

Название: {deal.title}
Статус: {deal.status}
Сумма: {deal.amount or 0} руб.

<a href="/deals/{deal.id}">Открыть сделку</a>
"""
    await send_telegram_message(user.telegram_id, message)


async def notify_new_task_telegram(user: User, task: Task):
    """Уведомление о новой задаче"""
    if not user.telegram_id:
        return

    message = f"""
✅ <b>Новая задача</b>

{task.title}
Приоритет: {task.priority}
Срок: {task.due_date.strftime('%d.%m.%Y') if task.due_date else 'Не указан'}
"""
    await send_telegram_message(user.telegram_id, message)


# ============ BOT WEBHOOK ============

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Webhook для входящих сообщений от Telegram бота"""
    data = await request.json()

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    username = message.get("from", {}).get("username")

    # Команды бота
    if text == "/start":
        reply = """
👋 Привет! Я бот Мир Самозанятых.

Команды:
/status — статистика
/tasks — список задач
/deals — активные сделки
/help — помощь

Подключите меня в настройках профиля.
"""
        await send_telegram_message(str(chat_id), reply)

    elif text == "/status":
        # Найти пользователя по telegram_id
        result = await db.execute(
            select(User).where(User.telegram_id == str(chat_id))
        )
        user = result.scalar_one_or_none()

        if user:
            reply = f"""
📊 <b>Статистика</b>

Клиентов: (данные из CRM)
Сделок: (данные из CRM)
Задач: (данные из CRM)

Тариф: {user.tier}
"""
        else:
            reply = "❌ Аккаунт не привязан. Подключите Telegram в настройках профиля."

        await send_telegram_message(str(chat_id), reply)

    elif text == "/help":
        reply = """
📖 <b>Помощь</b>

/status — статистика
/tasks — задачи
/deals — сделки
/settings — настройки

Для подключения:
1. Войдите в личный кабинет
2. Настройки → Telegram
3. Нажмите "Подключить"
"""
        await send_telegram_message(str(chat_id), reply)

    return {"ok": True}
