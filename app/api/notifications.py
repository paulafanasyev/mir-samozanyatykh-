"""
API уведомлений v7.6
In-app уведомления + email + WebSocket push + массовая рассылка
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import logger, log_audit
from app.models import User, Notification
from app.api.admin import require_admin
from app.services.email import email_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ============ SCHEMAS ============

class NotificationCreate(BaseModel):
    title: str = Field(..., max_length=255)
    body: str = Field(..., max_length=2000)
    notification_type: str = Field("info", pattern=r"^(info|warning|success|error)$")
    action_url: Optional[str] = Field(None, max_length=500)
    data: Optional[dict] = None


class NotificationOut(BaseModel):
    id: int
    title: str
    body: str
    notification_type: str
    is_read: bool
    action_url: Optional[str]
    data: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class BulkNotification(BaseModel):
    title: str = Field(..., max_length=255)
    body: str = Field(..., max_length=2000)
    notification_type: str = Field("info", pattern=r"^(info|warning|success|error)$")
    action_url: Optional[str] = Field(None, max_length=500)
    target_tier: Optional[str] = Field(None, pattern=r"^(free|pro|business|enterprise)$")
    send_email: bool = False


class BulkNotificationResponse(BaseModel):
    sent_count: int
    email_sent: int
    failed: int


class NotificationPreferences(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    marketing_enabled: bool = True
    invoice_notifications: bool = True
    deal_notifications: bool = True
    task_reminders: bool = True


# ============ USER NOTIFICATIONS ============

@router.get("/", response_model=List[NotificationOut])
async def list_notifications(
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список уведомлений пользователя с пагинацией"""
    query = select(Notification).where(Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)

    count = await db.scalar(
        select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
    )

    result = await db.execute(
        query.order_by(desc(Notification.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    notifications = result.scalars().all()
    return [
        NotificationOut.model_validate(n) for n in notifications
    ]


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Количество непрочитанных уведомлений"""
    count = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    return {"unread_count": count}


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=NotificationOut)
async def create_notification(
    notification: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Создание уведомления (для тестирования)"""
    db_notification = Notification(
        user_id=current_user.id,
        **notification.model_dump(exclude_unset=True),
    )
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    return NotificationOut.model_validate(db_notification)


@router.put("/{notification_id}/read", response_model=NotificationOut)
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отметить уведомление как прочитанное"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return NotificationOut.model_validate(notification)


@router.put("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отметить все уведомления как прочитанные"""
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"message": f"Отмечено прочитанным: {result.rowcount}"}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление уведомления"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")

    await db.delete(notification)
    await db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удалить все прочитанные уведомления"""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == True,
        )
    )
    notifications = result.scalars().all()
    for n in notifications:
        await db.delete(n)
    await db.commit()


# ============ ADMIN BULK NOTIFICATIONS ============

@router.post("/admin/bulk", response_model=BulkNotificationResponse)
async def send_bulk_notification(
    bulk: BulkNotification,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Массовая рассылка уведомлений (только админ)"""
    query = select(User).where(User.is_active == True)
    if bulk.target_tier:
        query = query.where(User.subscription_tier == bulk.target_tier)

    result = await db.execute(query)
    users = result.scalars().all()

    sent_count = 0
    email_sent = 0
    failed = 0

    for user in users:
        try:
            notification = Notification(
                user_id=user.id,
                title=bulk.title,
                body=bulk.body,
                notification_type=bulk.notification_type,
                action_url=bulk.action_url,
            )
            db.add(notification)
            sent_count += 1

            if bulk.send_email and user.email:
                email_service.send_notification_email(
                    to_email=user.email,
                    subject=bulk.title,
                    body=bulk.body,
                )
                email_sent += 1

        except Exception as e:
            logger.error(f"Failed to send notification to user {user.id}: {e}")
            failed += 1

    await db.commit()

    await log_audit(
        action="admin_bulk_notification",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Sent to {sent_count} users, email={email_sent}, failed={failed}",
    )

    return BulkNotificationResponse(
        sent_count=sent_count,
        email_sent=email_sent,
        failed=failed,
    )


# ============ NOTIFICATION SERVICE HELPERS ============

async def notify_user(
    db: AsyncSession,
    user_id: int,
    title: str,
    body: str,
    notification_type: str = "info",
    action_url: Optional[str] = None,
    data: Optional[dict] = None,
) -> Notification:
    """Создать уведомление для пользователя (сервисная функция)"""
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type,
        action_url=action_url,
        data=data or {},
    )
    db.add(notification)
    await db.flush()
    return notification


async def notify_invoice_paid(
    db: AsyncSession,
    user_id: int,
    invoice_number: str,
    amount: float,
):
    """Уведомление об оплате счёта"""
    return await notify_user(
        db, user_id,
        title="Счёт оплачен!",
        body=f"Счёт {invoice_number} на сумму {amount} руб. успешно оплачен.",
        notification_type="success",
        action_url=f"/invoices",
    )


async def notify_new_client(
    db: AsyncSession,
    user_id: int,
    client_name: str,
):
    """Уведомление о новом клиенте"""
    return await notify_user(
        db, user_id,
        title="Новый клиент",
        body=f"Клиент {client_name} добавлен в вашу базу.",
        notification_type="info",
        action_url="/clients",
    )


async def notify_deal_won(
    db: AsyncSession,
    user_id: int,
    deal_title: str,
    amount: Optional[float] = None,
):
    """Уведомление о выигранной сделке"""
    body = f"Сделка \"{deal_title}\" перешла в статус \"Выиграна\""
    if amount:
        body += f" на сумму {amount} руб."
    return await notify_user(
        db, user_id,
        title="Сделка выиграна!",
        body=body,
        notification_type="success",
        action_url="/deals",
    )


async def notify_task_due(
    db: AsyncSession,
    user_id: int,
    task_title: str,
    due_date: datetime,
):
    """Напоминание о задаче"""
    return await notify_user(
        db, user_id,
        title="Напоминание о задаче",
        body=f"Задача \"{task_title}\" должна быть выполнена {due_date.strftime('%d.%m.%Y %H:%M')}",
        notification_type="warning",
        action_url="/dashboard",
    )
