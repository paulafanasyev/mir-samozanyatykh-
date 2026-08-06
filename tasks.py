"""
Celery tasks for Мир Самозанятых
Асинхронные задачи: email, SMS, уведомления, напоминания
"""

import os
import asyncio
from datetime import datetime, timedelta, timezone
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func

from server import settings as app_settings

# Celery app
celery_app = Celery(
    "mir_samozanyatykh",
    broker=app_settings.REDIS_URL,
    backend=app_settings.REDIS_URL,
    include=["tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "check-overdue-invoices": {
            "task": "tasks.check_overdue_invoices",
            "schedule": 3600.0,
        },
        "daily-summary": {
            "task": "tasks.send_daily_summary",
            "schedule": 86400.0,
        },
        "check-pending-payments": {
            "task": "tasks.check_pending_yookassa_payments",
            "schedule": 300.0,
        },
    }
)


# WebSocket notification helper (called from Celery tasks)
async def ws_notify_user(user_id: int, title: str, message: str, notification_type: str = "info"):
    """Send real-time notification via WebSocket"""
    try:
        import httpx
        # In production, use Redis pub/sub or direct WebSocket broadcast
        # For now, we store notification in DB and client polls
        pass
    except Exception as e:
        print(f"[WebSocket notify error] {e}")

engine = create_async_engine(app_settings.DATABASE_URL, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to_email: str, subject: str, body: str, html_body: str = None):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if not app_settings.SMTP_HOST:
            return {"status": "skipped", "reason": "smtp_not_configured"}

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = app_settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP_SSL(app_settings.SMTP_HOST, app_settings.SMTP_PORT) as server:
                server.login(app_settings.SMTP_USER, app_settings.SMTP_PASSWORD)
                server.sendmail(app_settings.SMTP_USER, [to_email], msg.as_string())
        except smtplib.SMTPException as e:
            # Never log credentials
            raise self.retry(exc=e)
        return {"status": "sent", "to": to_email}
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(self, phone: str, message: str):
    try:
        import httpx
        api_key = os.environ.get("SMS_RU_API_KEY", "")
        if not api_key:
            return {"status": "skipped", "reason": "sms_not_configured"}
        response = httpx.get("https://sms.ru/sms/send", params={"api_id": api_key, "to": phone, "msg": message, "json": 1})
        data = response.json()
        return {"status": "sent" if data.get("status") == "OK" else "failed", "response": data}
    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task
def create_notification_task(user_id: int, title: str, message: str, notification_type: str = "info"):
    async def _create():
        async with async_session() as db:
            from server import Notification
            db.add(Notification(user_id=user_id, title=title, message=message, type=notification_type))
            await db.commit()
            # Attempt WebSocket notification (best effort)
            try:
                await ws_notify_user(user_id, title, message, notification_type)
            except Exception:
                pass
    asyncio.run(_create())
    return {"status": "created"}

@celery_app.task
def check_overdue_invoices():
    async def _check():
        async with async_session() as db:
            from server import Invoice, User, Notification
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(Invoice, User).join(User, Invoice.user_id == User.id)
                .where(Invoice.status == "sent", Invoice.due_date < now)
            )
            overdue = result.all()
            for invoice, user in overdue:
                invoice.status = "overdue"
                db.add(Notification(user_id=user.id, title="⚠️ Просрочен счёт",
                    message=f"Счёт {invoice.invoice_number} просрочен. Сумма: {invoice.total_amount} ₽", type="warning"))
                if user.email and app_settings.SMTP_HOST:
                    send_email_task.delay(user.email, "Просрочен счёт — Мир Самозанятых",
                        f"Счёт {invoice.invoice_number} просрочен. Сумма: {invoice.total_amount} ₽.")
            await db.commit()
            return {"overdue_count": len(overdue)}
    return asyncio.run(_check())

@celery_app.task
def send_daily_summary():
    async def _send():
        async with async_session() as db:
            from server import User, Invoice
            result = await db.execute(select(User).where(User.is_active == True))
            users = result.scalars().all()
            for user in users:
                today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                inv_result = await db.execute(select(func.count(Invoice.id), func.sum(Invoice.total_amount))
                    .where(Invoice.user_id == user.id, Invoice.created_at >= today))
                invoices_count, invoices_sum = inv_result.first() or (0, 0)
                paid_result = await db.execute(select(func.sum(Invoice.total_amount))
                    .where(Invoice.user_id == user.id, Invoice.status == "paid", Invoice.paid_at >= today))
                paid_today = paid_result.scalar() or 0
                if invoices_count > 0 or paid_today > 0:
                    msg = f"📊 Сводка за сегодня:
• Новых счетов: {invoices_count} на {(invoices_sum or 0):.0f} ₽
• Получено: {paid_today:.0f} ₽"
                    db.add(Notification(user_id=user.id, title="📊 Ежедневная сводка", message=msg, type="info"))
            await db.commit()
            return {"users_notified": len(users)}
    return asyncio.run(_send())

@celery_app.task
def check_pending_yookassa_payments():
    async def _check():
        import httpx, base64
        if not app_settings.YOOKASSA_SHOP_ID or not app_settings.YOOKASSA_SECRET_KEY:
            return {"status": "skipped"}
        async with async_session() as db:
            from server import Invoice, Payment
            result = await db.execute(select(Invoice).where(
                Invoice.status == "sent", Invoice.yookassa_payment_id.isnot(None)))
            pending = result.scalars().all()
            auth = base64.b64encode(f"{app_settings.YOOKASSA_SHOP_ID}:{app_settings.YOOKASSA_SECRET_KEY}".encode()).decode()
            updated = 0
            for invoice in pending:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(f"https://api.yookassa.ru/v3/payments/{invoice.yookassa_payment_id}",
                            headers={"Authorization": f"Basic {auth}"})
                        data = response.json()
                        if data.get("status") == "succeeded":
                            invoice.status = "paid"
                            invoice.paid_at = datetime.now(timezone.utc)
                            db.add(Payment(invoice_id=invoice.id, amount=invoice.total_amount, payment_method="card",
                                status="completed", yookassa_id=invoice.yookassa_payment_id, paid_at=datetime.now(timezone.utc)))
                            updated += 1
                        elif data.get("status") == "canceled":
                            invoice.status = "cancelled"
                except Exception as e:
                    print(f"[YooKassa check error] {e}")
            await db.commit()
            return {"checked": len(pending), "updated": updated}
    return asyncio.run(_check())
