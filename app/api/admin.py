"""
API админ-панели v7.5
Управление пользователями, модерация, аудит-логи, статистика платформы
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import logger, log_audit
from app.core.config import settings
from app.models import User, UserSession, AuditLog, Invoice, Payment, Client, Deal
from app.schemas.admin import (
    AdminUserUpdate, AdminUserOut, UserListResponse,
    PlatformStats, AuditLogOut, AuditLogListResponse,
    BulkTierUpdate, BulkTierResponse, ModerationAction,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============ DEPENDENCIES ============

async def require_admin(current_user: User = Depends(get_current_user)):
    """Проверка прав администратора"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return current_user


async def require_moderator(current_user: User = Depends(get_current_user)):
    """Проверка прав модератора или администратора"""
    if not current_user.is_admin and not current_user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права модератора",
        )
    return current_user


# ============ USERS MANAGEMENT ============

@router.get("/users", response_model=UserListResponse)
async def list_users(
    request: Request,
    search: Optional[str] = None,
    tier: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern=r"^(created_at|email|full_name|last_login_at|subscription_tier)$"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Список всех пользователей с фильтрами и пагинацией"""
    query = select(User)
    
    # Фильтры
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_filter)) |
            (User.full_name.ilike(search_filter)) |
            (User.phone.ilike(search_filter)) |
            (User.inn.ilike(search_filter))
        )
    if tier:
        query = query.where(User.subscription_tier == tier)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)
    
    # Сортировка
    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Пагинация
    count_query = select(func.count(User.id))
    if search:
        count_query = count_query.where(
            (User.email.ilike(search_filter)) |
            (User.full_name.ilike(search_filter)) |
            (User.phone.ilike(search_filter)) |
            (User.inn.ilike(search_filter))
        )
    if tier:
        count_query = count_query.where(User.subscription_tier == tier)
    if is_active is not None:
        count_query = count_query.where(User.is_active == is_active)
    if is_verified is not None:
        count_query = count_query.where(User.is_verified == is_verified)
    
    total = await db.scalar(count_query)
    
    result = await db.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    users = result.scalars().all()
    
    await log_audit(
        action="admin_users_list",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Page {page}, search={search}, tier={tier}",
    )
    
    return UserListResponse(
        users=[AdminUserOut.model_validate(u) for u in users],
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    )


@router.get("/users/{user_id}", response_model=AdminUserOut)
async def get_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Детали пользователя по ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    await log_audit(
        action="admin_user_view",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Viewed user {user_id}",
    )
    return AdminUserOut.model_validate(user)


@router.put("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: int,
    update: AdminUserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Обновление пользователя администратором"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя редактировать себя через этот endpoint (безопасность)
    if user.id == admin.id and update.is_admin is False:
        raise HTTPException(status_code=400, detail="Нельзя снять с себя права администратора")
    
    update_data = update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    
    await log_audit(
        action="admin_user_updated",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Updated user {user_id}: {update_data}",
    )
    return AdminUserOut.model_validate(user)


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    action: ModerationAction,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Блокировка пользователя"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя заблокировать себя")
    
    user.is_active = False
    if action.duration_hours:
        user.locked_until = datetime.now(timezone.utc) + timedelta(hours=action.duration_hours)
    
    # Отзыв всех сессий
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id)
        .values(revoked=True)
    )
    
    await db.commit()
    
    await log_audit(
        action="admin_user_blocked",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Blocked user {user_id}, reason={action.reason}, duration={action.duration_hours}h",
    )
    return {
        "message": f"Пользователь {user.email} заблокирован",
        "blocked_until": user.locked_until.isoformat() if user.locked_until else None,
        "reason": action.reason,
    }


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Разблокировка пользователя"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.is_active = True
    user.locked_until = None
    user.failed_login_attempts = 0
    await db.commit()
    
    await log_audit(
        action="admin_user_unblocked",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Unblocked user {user_id}",
    )
    return {"message": f"Пользователь {user.email} разблокирован"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Удаление пользователя (GDPR — полное удаление)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")
    
    email = user.email
    await db.delete(user)
    await db.commit()
    
    await log_audit(
        action="admin_user_deleted",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Deleted user {user_id} ({email})",
    )


# ============ BULK TIER OPERATIONS ============

@router.post("/users/bulk/tier", response_model=BulkTierResponse)
async def bulk_update_tier(
    bulk: BulkTierUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Массовое изменение тарифа подписок"""
    expires_at = datetime.now(timezone.utc) + timedelta(days=bulk.expires_days)
    updated = 0
    failed = 0
    errors = []
    
    for user_id in bulk.user_ids:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                failed += 1
                errors.append(f"User {user_id} not found")
                continue
            
            user.subscription_tier = bulk.tier
            user.subscription_expires = expires_at
            updated += 1
            
        except Exception as e:
            failed += 1
            errors.append(f"User {user_id}: {str(e)}")
    
    await db.commit()
    
    await log_audit(
        action="admin_bulk_tier_update",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Updated {updated} users to tier {bulk.tier}, failed {failed}",
    )
    
    return BulkTierResponse(
        updated=updated,
        failed=failed,
        errors=errors,
        tier=bulk.tier,
        expires_at=expires_at,
    )


# ============ PLATFORM STATISTICS ============

@router.get("/stats", response_model=PlatformStats)
async def platform_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Общая статистика платформы"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    # Пользователи
    total_users = await db.scalar(select(func.count(User.id)))
    active_users_30d = await db.scalar(
        select(func.count(User.id)).where(User.last_login_at >= month_start)
    )
    new_users_today = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    new_users_week = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= week_start)
    )
    new_users_month = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= month_start)
    )
    
    # Выручка
    total_revenue = await db.scalar(
        select(func.sum(Invoice.total_amount)).where(Invoice.status == "paid")
    ) or 0
    paid_invoices_count = await db.scalar(
        select(func.count(Invoice.id)).where(Invoice.status == "paid")
    )
    
    # Подписки по тарифам
    tier_counts = {}
    for tier in ["free", "pro", "business", "enterprise"]:
        count = await db.scalar(
            select(func.count(User.id)).where(User.subscription_tier == tier)
        )
        total = total_users or 1
        tier_counts[tier] = {
            "count": count,
            "percentage": round(count / total * 100, 1),
        }
    
    # Среднее количество счетов на пользователя
    total_invoices = await db.scalar(select(func.count(Invoice.id)))
    avg_invoices = round(total_invoices / (total_users or 1), 2)
    
    # Топ действий в аудит-логах
    top_actions_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id).label("count"))
        .group_by(AuditLog.action)
        .order_by(desc("count"))
        .limit(10)
    )
    top_actions = [{"action": a.action, "count": a.count} for a in top_actions_result.all()]
    
    # Пользователи по месяцам (последние 12)
    users_by_month = []
    for i in range(11, -1, -1):
        month_start_date = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start_date + timedelta(days=32)).replace(day=1)
        count = await db.scalar(
            select(func.count(User.id)).where(
                User.created_at >= month_start_date,
                User.created_at < month_end,
            )
        )
        users_by_month.append({
            "month": month_start_date.strftime("%Y-%m"),
            "count": count,
        })
    
    await log_audit(
        action="admin_stats_viewed",
        user_id=admin.id,
        ip_address=request.client.host,
    )
    
    return PlatformStats(
        total_users=total_users,
        active_users_30d=active_users_30d,
        new_users_today=new_users_today,
        new_users_week=new_users_week,
        new_users_month=new_users_month,
        total_revenue=float(total_revenue),
        paid_invoices_count=paid_invoices_count,
        subscriptions_by_tier=tier_counts,
        avg_invoices_per_user=avg_invoices,
        top_actions=top_actions,
        users_by_month=users_by_month,
    )


@router.get("/stats/revenue-chart")
async def revenue_chart_admin(
    months: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """График выручки по месяцам для админ-панели"""
    now = datetime.now(timezone.utc)
    data = []
    
    for i in range(months - 1, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        revenue = await db.scalar(
            select(func.sum(Invoice.total_amount)).where(
                Invoice.status == "paid",
                Invoice.paid_at >= month_start,
                Invoice.paid_at < month_end,
            )
        ) or 0
        
        count = await db.scalar(
            select(func.count(Invoice.id)).where(
                Invoice.status == "paid",
                Invoice.paid_at >= month_start,
                Invoice.paid_at < month_end,
            )
        )
        
        data.append({
            "month": month_start.strftime("%Y-%m"),
            "revenue": float(revenue),
            "invoices": count,
        })
    
    return {"chart_data": data}


# ============ AUDIT LOGS ============

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    request: Request,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Просмотр всех аудит-логов с фильтрами"""
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    
    # Фильтры
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (AuditLog.details.ilike(search_filter)) |
            (AuditLog.resource.ilike(search_filter))
        )
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    # Подсчёт
    count_query = select(func.count(AuditLog.id))
    if user_id:
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        count_query = count_query.where(AuditLog.action == action)
    if search:
        count_query = count_query.where(
            (AuditLog.details.ilike(search_filter)) |
            (AuditLog.resource.ilike(search_filter))
        )
    if start_date:
        count_query = count_query.where(AuditLog.created_at >= start_date)
    if end_date:
        count_query = count_query.where(AuditLog.created_at <= end_date)
    
    total = await db.scalar(count_query)
    
    result = await db.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    logs = result.scalars().all()
    
    # Добавляем email пользователя
    log_outs = []
    for log in logs:
        user_email = None
        if log.user_id:
            user_result = await db.execute(
                select(User.email).where(User.id == log.user_id)
            )
            user_email = user_result.scalar_one_or_none()
        
        log_data = AuditLogOut.model_validate(log)
        log_outs.append(log_data.model_copy(update={"user_email": user_email}))
    
    await log_audit(
        action="admin_audit_logs_viewed",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Page {page}, user_id={user_id}, action={action}",
    )
    
    return AuditLogListResponse(
        logs=log_outs,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    )


@router.get("/audit-logs/actions")
async def list_audit_actions(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Список всех уникальных действий в аудит-логах"""
    result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id).label("count"))
        .group_by(AuditLog.action)
        .order_by(desc("count"))
    )
    return [{"action": r.action, "count": r.count} for r in result.all()]


# ============ USER AUDIT LOGS (for moderators too) ============

@router.get("/users/{user_id}/audit-logs", response_model=AuditLogListResponse)
async def user_audit_logs(
    user_id: int,
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    """Аудит-логи конкретного пользователя"""
    query = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(desc(AuditLog.created_at))
    )
    
    total = await db.scalar(
        select(func.count(AuditLog.id)).where(AuditLog.user_id == user_id)
    )
    
    result = await db.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    logs = result.scalars().all()
    
    # Email пользователя
    user_result = await db.execute(select(User.email).where(User.id == user_id))
    user_email = user_result.scalar_one_or_none()
    
    log_outs = []
    for log in logs:
        log_data = AuditLogOut.model_validate(log)
        log_outs.append(log_data.model_copy(update={"user_email": user_email}))
    
    await log_audit(
        action="admin_user_audit_viewed",
        user_id=moderator.id,
        ip_address=request.client.host,
        details=f"Viewed audit logs for user {user_id}",
    )
    
    return AuditLogListResponse(
        logs=log_outs,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    )


# ============ SESSIONS MANAGEMENT ============

@router.get("/users/{user_id}/sessions")
async def list_user_sessions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Активные сессии пользователя"""
    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked == False,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        .order_by(desc(UserSession.created_at))
    )
    sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "id": s.id,
                "token_type": s.token_type,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            }
            for s in sessions
        ]
    }


@router.post("/users/{user_id}/sessions/revoke-all")
async def revoke_all_sessions(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Отзыв всех сессий пользователя (force logout)"""
    result = await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id)
        .values(revoked=True)
    )
    await db.commit()
    
    await log_audit(
        action="admin_sessions_revoked",
        user_id=admin.id,
        ip_address=request.client.host,
        details=f"Revoked all sessions for user {user_id}",
    )
    return {"message": f"Все сессии пользователя отозваны", "revoked_count": result.rowcount}
