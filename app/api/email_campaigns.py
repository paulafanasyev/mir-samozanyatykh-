"""
API email-рассылок v6.8
Массовые рассылки клиентам через SMTP
"""

from datetime import datetime, timezone
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.core.config import settings
from app.models import User, Client
from app.services.email import send_email

router = APIRouter(prefix="/api/email", tags=["email"])


class EmailCampaignCreate(BaseModel):
    name: str
    subject: str
    body: str
    client_ids: Optional[List[int]] = None  # None = всем клиентам
    send_now: bool = False


class EmailCampaignOut(BaseModel):
    id: int
    name: str
    subject: str
    status: str
    sent_count: int
    opened_count: int
    created_at: datetime


# ============ CAMPAIGNS ============

@router.get("/campaigns")
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список email-кампаний"""
    # Храним кампании в памяти (для простоты) или можно добавить модель
    return {"campaigns": [], "message": "Используйте POST /send для отправки"}


@router.post("/send")
async def send_email_campaign(
    campaign: EmailCampaignCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Массовая email-рассылка клиентам"""

    # Получаем список получателей
    if campaign.client_ids:
        result = await db.execute(
            select(Client).where(
                Client.user_id == current_user.id,
                Client.id.in_(campaign.client_ids),
                Client.email.isnot(None),
            )
        )
    else:
        result = await db.execute(
            select(Client).where(
                Client.user_id == current_user.id,
                Client.email.isnot(None),
            )
        )

    clients = result.scalars().all()
    recipients = [c.email for c in clients if c.email]

    if not recipients:
        raise HTTPException(status_code=400, detail="Нет клиентов с email")

    # Проверка лимитов тарифа
    tiers = {
        "free": 10, "pro": 100, "business": 1000, "enterprise": 10000
    }
    limit = tiers.get(current_user.tier, 10)
    if len(recipients) > limit:
        raise HTTPException(
            status_code=403,
            detail=f"Лимит рассылки: {limit} писем. У вас {len(recipients)} получателей."
        )

    # Отправка в фоне
    background_tasks.add_task(
        _send_bulk_email,
        recipients=recipients,
        subject=campaign.subject,
        body=campaign.body,
        sender_name=current_user.full_name or settings.APP_NAME,
    )

    await log_audit(
        action="email_campaign_sent",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Campaign: {campaign.name}, recipients: {len(recipients)}",
    )

    return {
        "message": "Рассылка запущена",
        "recipients_count": len(recipients),
        "campaign_name": campaign.name,
    }


@router.post("/send-single")
async def send_single_email(
    client_id: int,
    subject: str,
    body: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отправка письма одному клиенту"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()
    if not client or not client.email:
        raise HTTPException(status_code=404, detail="Клиент не найден или нет email")

    success = await send_email(
        to_email=client.email,
        subject=subject,
        body=body,
    )

    await log_audit(
        action="email_sent",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"To: {client.email}, subject: {subject}",
    )

    return {"message": "Письмо отправлено" if success else "Ошибка отправки"}


# ============ BACKGROUND TASK ============

def _send_bulk_email(recipients: List[str], subject: str, body: str, sender_name: str):
    """Фоновая отправка массовой рассылки"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{settings.SMTP_USER}>"
        msg["To"] = ", ".join(recipients[:50])  # BCC для больших списков

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                {body}
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                <p style="font-size: 12px; color: #666;">
                    Вы получили это письмо, так являетесь клиентом {sender_name}.<br>
                    <a href="#">Отписаться от рассылки</a>
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, recipients, msg.as_string())

    except Exception as e:
        import logging
        logging.error(f"Bulk email error: {e}")
