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
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.core.logging import log_audit
from app.core.auth import get_current_user, get_current_user_optional
from app.core.config import settings
from app.models import User, Client, EmailCampaign
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
    result = await db.execute(
        select(EmailCampaign).where(EmailCampaign.user_id == current_user.id).order_by(EmailCampaign.created_at.desc())
    )
    campaigns = result.scalars().all()
    return {"campaigns": [
        {
            "id": c.id, "name": c.name, "subject": c.subject, "status": c.status,
            "sent_count": c.sent_count, "opened_count": c.opened_count, "created_at": c.created_at,
            "recipient_count": c.recipient_count, "error_message": c.error_message,
        } for c in campaigns
    ]}


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
    limit = tiers.get(current_user.user_tier, 10)
    if len(recipients) > limit:
        raise HTTPException(
            status_code=403,
            detail=f"Лимит рассылки: {limit} писем. У вас {len(recipients)} получателей."
        )

    db_campaign = EmailCampaign(
        user_id=current_user.id, name=campaign.name.strip(), subject=campaign.subject.strip(),
        body=campaign.body, status="queued", recipient_count=len(recipients), sent_count=0,
    )
    db.add(db_campaign)
    await db.commit()
    await db.refresh(db_campaign)

    background_tasks.add_task(
        _send_bulk_email,
        campaign_id=db_campaign.id, recipients=recipients, subject=campaign.subject,
        body=campaign.body, sender_name=current_user.full_name or settings.APP_NAME,
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
        "campaign_id": db_campaign.id,
    }


@router.post("/send-single")
@rate_limit("20/minute")
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
        action="email_sent" if success else "email_send_failed",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"To: {client.email}, subject: {subject}, success={success}",
    )

    if not success:
        raise HTTPException(status_code=502, detail="Почтовый сервис временно недоступен")
    return {"message": "Письмо отправлено"}


# ============ BACKGROUND TASK ============

def _send_bulk_email(campaign_id: int, recipients: List[str], subject: str, body: str, sender_name: str):
    """Фоновая отправка с сохранением результата кампании."""
    from html import escape
    import asyncio
    from app.core.database import async_session
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{settings.SMTP_USER}>"
        msg["Bcc"] = ", ".join(recipients)
        safe_body = escape(body).replace("&lt;br&gt;", "<br>")
        html_body = f"<html><body>{safe_body}</body></html>"
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(MIMEText(body, "plain", "utf-8"))

        if settings.SMTP_TLS and settings.SMTP_PORT == 465:
            smtp = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
        else:
            smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            if settings.SMTP_TLS:
                smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.SMTP_USER, recipients, msg.as_string())
        smtp.quit()

        async def mark_done():
            async with async_session() as session:
                await session.execute(update(EmailCampaign).where(EmailCampaign.id == campaign_id).values(status="completed", sent_count=len(recipients), completed_at=datetime.now(timezone.utc)))
                await session.commit()
        asyncio.run(mark_done())
    except Exception:
        async def mark_failed():
            async with async_session() as session:
                await session.execute(update(EmailCampaign).where(EmailCampaign.id == campaign_id).values(status="failed", error_message="Email provider temporarily unavailable", completed_at=datetime.now(timezone.utc)))
                await session.commit()
        try:
            asyncio.run(mark_failed())
        except Exception:
            pass
