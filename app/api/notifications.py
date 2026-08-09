"""
API уведомлений v8.4
In-app + email + WebSocket push + Web Push + Telegram + настройки
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
from app.models import User, Notification, PushSubscription, NotificationPreference
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


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    device_info: Optional[str] = None


class PushSubscriptionOut(BaseModel):
    id: int
    endpoint: str
    device_info: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None
    invoice_paid: Optional[bool] = None
    invoice_overdue: Optional[bool] = None
    new_client: Optional[bool] = None
    deal_won: Optional[bool] = None
    deal_lost: Optional[bool] = None
    task_reminder: Optional[bool] = None
    task_overdue: Optional[bool] = None
    bank_sync: Optional[bool] = None
    tax_reminder: Optional[bool] = None
    marketing: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)


class NotificationPreferencesOut(BaseModel):
    email_enabled: bool
    push_enabled: bool
    telegram_enabled: bool
    telegram_chat_id: Optional[str]
    invoice_paid: bool
    invoice_overdue: bool
    new_client: bool
    deal_won: bool
    deal_lost: bool
    task_reminder: bool
    task_overdue: bool
    bank_sync: bool
    tax_reminder: bool
    marketing: bool
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]

    class Config:
        from_attributes = True


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
    return [NotificationOut.model_validate(n) for n in notifications]


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
    """Создание уведомления"""
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


# ============ PUSH SUBSCRIPTIONS ============

@router.post("/push/subscribe", response_model=PushSubscriptionOut)
async def subscribe_push(
    sub: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Подписка на push-уведомления (Web Push API)"""
    # Проверяем, нет ли уже такой подписки
    existing = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == current_user.id,
            PushSubscription.endpoint == sub.endpoint,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Подписка уже существует")

    subscription = PushSubscription(
        user_id=current_user.id,
        endpoint=sub.endpoint,
        p256dh=sub.p256dh,
        auth=sub.auth,
        device_info=sub.device_info,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    logger.info(f"Push subscription created for user {current_user.id}")
    return PushSubscriptionOut.model_validate(subscription)


@router.get("/push/subscriptions", response_model=List[PushSubscriptionOut])
async def list_push_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список push-подписок пользователя"""
    result = await db.execute(
        select(PushSubscription)
        .where(PushSubscription.user_id == current_user.id)
        .order_by(desc(PushSubscription.created_at))
    )
    return result.scalars().all()


@router.delete("/push/subscriptions/{sub_id}", status_code=204)
async def unsubscribe_push(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отписка от push-уведомлений"""
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.id == sub_id,
            PushSubscription.user_id == current_user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Подписка не найдена")
    await db.delete(sub)
    await db.commit()


# ============ NOTIFICATION PREFERENCES ============

@router.get("/preferences", response_model=NotificationPreferencesOut)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить настройки уведомлений"""
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user.id
        )
    )
    pref = result.scalar_one_or_none()
    if not pref:
        # Создаем дефолтные настройки
        pref = NotificationPreference(user_id=current_user.id)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return NotificationPreferencesOut.model_validate(pref)


@router.put("/preferences", response_model=NotificationPreferencesOut)
async def update_preferences(
    update: NotificationPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Обновить настройки уведомлений"""
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == current_user.id
        )
    )
    pref = result.scalar_one_or_none()
    if not pref:
        pref = NotificationPreference(user_id=current_user.id)
        db.add(pref)

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(pref, key, value)

    await db.commit()
    await db.refresh(pref)
    return NotificationPreferencesOut.model_validate(pref)


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
    """Создать уведомление для пользователя"""
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
        action_url="/invoices",
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
    body = f'Сделка "{deal_title}" перешла в статус "Выиграна"'
    if amount:
        body += f" на сумму {amount} руб."
    return await notify_user(
        db, user_id,
        title="Сделка выиграна!",
        body=body,
        notification_type="success",
        action_url="/deals",
    )


async def notify_deal_lost(
    db: AsyncSession,
    user_id: int,
    deal_title: str,
):
    """Уведомление о проигранной сделке"""
    return await notify_user(
        db, user_id,
        title="Сделка проиграна",
        body=f'Сделка "{deal_title}" перешла в статус "Проиграна"',
        notification_type="warning",
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
        body=f'Задача "{task_title}" должна быть выполнена {due_date.strftime("%d.%m.%Y %H:%M")}',
        notification_type="warning",
        action_url="/dashboard",
    )


async def notify_bank_sync(
    db: AsyncSession,
    user_id: int,
    bank_name: str,
    imported: int,
):
    """Уведомление о синхронизации банка"""
    return await notify_user(
        db, user_id,
        title="Синхронизация завершена",
        body=f"Импортировано {imported} операций из {bank_name}.",
        notification_type="success",
        action_url="/accounting",
    )
