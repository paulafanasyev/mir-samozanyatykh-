"""
API для Flutter мобильного приложения v6.7
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Client, Deal, Invoice, Task, Call
from app.core.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/flutter", tags=["flutter"])


@router.get("/dashboard")
async def flutter_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Дашборд для Flutter — компактные данные"""
    clients_count = await db.scalar(
        select(func.count(Client.id)).where(Client.user_id == current_user.id)
    )
    deals_count = await db.scalar(
        select(func.count(Deal.id)).where(Deal.user_id == current_user.id)
    )
    won_deals = await db.scalar(
        select(func.count(Deal.id)).where(
            Deal.user_id == current_user.id, Deal.status == "won"
        )
    )
    invoices_count = await db.scalar(
        select(func.count(Invoice.id)).where(Invoice.user_id == current_user.id)
    )
    pending_invoices = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.status.in_(["draft", "sent"]),
        )
    )
    pending_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status.in_(["pending", "in_progress"]),
        )
    )
    recent_calls = await db.scalar(
        select(func.count(Call.id)).where(
            Call.user_id == current_user.id,
            Call.created_at > datetime.now(timezone.utc).replace(hour=0, minute=0),
        )
    )

    return {
        "stats": {
            "clients": clients_count,
            "deals": {"total": deals_count, "won": won_deals},
            "invoices": {"total": invoices_count, "pending": pending_invoices},
            "tasks": pending_tasks,
            "calls_today": recent_calls,
        },
        "user": {
            "id": current_user.id,
            "name": current_user.full_name or current_user.email,
            "email": current_user.email,
            "tier": current_user.user_tier,
        },
    }


@router.get("/clients/sync")
async def sync_clients(
    last_sync: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Синхронизация клиентов для Flutter"""
    query = select(Client).where(Client.user_id == current_user.id)
    if last_sync:
        query = query.where(Client.updated_at > last_sync)
    result = await db.execute(query.order_by(Client.updated_at.desc()))
    return {
        "clients": result.scalars().all(),
        "sync_time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/deals/sync")
async def sync_deals(
    last_sync: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Синхронизация сделок для Flutter"""
    query = select(Deal).where(Deal.user_id == current_user.id)
    if last_sync:
        query = query.where(Deal.updated_at > last_sync)
    result = await db.execute(query.order_by(Deal.updated_at.desc()))
    return {
        "deals": result.scalars().all(),
        "sync_time": datetime.now(timezone.utc).isoformat(),
    }
