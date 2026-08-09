"""
API аналитики v6.8
Графики, отчёты, статистика
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Client, Deal, Invoice, Task, Call

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard")
async def analytics_dashboard(
    period: str = "month",  # week, month, quarter, year
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Аналитический дашборд"""

    now = datetime.now(timezone.utc)
    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    elif period == "quarter":
        start = now - timedelta(days=90)
    elif period == "year":
        start = now - timedelta(days=365)
    else:
        start = now - timedelta(days=30)

    # Клиенты
    new_clients = await db.scalar(
        select(func.count(Client.id)).where(
            Client.user_id == current_user.id,
            Client.created_at >= start,
        )
    )
    total_clients = await db.scalar(
        select(func.count(Client.id)).where(Client.user_id == current_user.id)
    )

    # Сделки
    deals_total = await db.scalar(
        select(func.count(Deal.id)).where(
            Deal.user_id == current_user.id,
            Deal.created_at >= start,
        )
    )
    deals_won = await db.scalar(
        select(func.count(Deal.id)).where(
            Deal.user_id == current_user.id,
            Deal.status == "won",
            Deal.created_at >= start,
        )
    )
    revenue = await db.scalar(
        select(func.sum(Deal.amount)).where(
            Deal.user_id == current_user.id,
            Deal.status == "won",
            Deal.created_at >= start,
        )
    ) or 0

    # Счета
    invoices_total = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.created_at >= start,
        )
    )
    invoices_paid = await db.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.user_id == current_user.id,
            Invoice.status == "paid",
            Invoice.created_at >= start,
        )
    )

    # Задачи
    tasks_completed = await db.scalar(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status == "completed",
            Task.completed_at >= start,
        )
    )

    # Звонки
    calls_total = await db.scalar(
        select(func.count(Call.id)).where(
            Call.user_id == current_user.id,
            Call.created_at >= start,
        )
    )
    calls_duration = await db.scalar(
        select(func.sum(Call.duration)).where(
            Call.user_id == current_user.id,
            Call.created_at >= start,
        )
    ) or 0

    return {
        "period": period,
        "clients": {"new": new_clients, "total": total_clients},
        "deals": {"total": deals_total, "won": deals_won, "conversion": round(deals_won/deals_total*100, 1) if deals_total else 0},
        "revenue": float(revenue),
        "invoices": {"total": invoices_total, "paid": invoices_paid},
        "tasks_completed": tasks_completed,
        "calls": {"total": calls_total, "duration_min": round(calls_duration/60, 1)},
    }


@router.get("/revenue-chart")
async def revenue_chart(
    months: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Данные для графика выручки по месяцам"""
    now = datetime.now(timezone.utc)
    data = []

    for i in range(months - 1, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)

        revenue = await db.scalar(
            select(func.sum(Deal.amount)).where(
                Deal.user_id == current_user.id,
                Deal.status == "won",
                Deal.created_at >= month_start,
                Deal.created_at < month_end,
            )
        ) or 0

        deals_count = await db.scalar(
            select(func.count(Deal.id)).where(
                Deal.user_id == current_user.id,
                Deal.status == "won",
                Deal.created_at >= month_start,
                Deal.created_at < month_end,
            )
        )

        data.append({
            "month": month_start.strftime("%Y-%m"),
            "revenue": float(revenue),
            "deals": deals_count,
        })

    return {"chart_data": data}


@router.get("/clients-chart")
async def clients_chart(
    months: int = 6,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Данные для графика роста клиентской базы"""
    now = datetime.now(timezone.utc)
    data = []

    for i in range(months - 1, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)

        new_clients = await db.scalar(
            select(func.count(Client.id)).where(
                Client.user_id == current_user.id,
                Client.created_at >= month_start,
                Client.created_at < month_end,
            )
        )

        total_clients = await db.scalar(
            select(func.count(Client.id)).where(
                Client.user_id == current_user.id,
                Client.created_at < month_end,
            )
        )

        data.append({
            "month": month_start.strftime("%Y-%m"),
            "new": new_clients,
            "total": total_clients,
        })

    return {"chart_data": data}


@router.get("/pipeline-chart")
async def pipeline_chart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Данные для графика воронки продаж"""
    from app.models import PipelineStage

    stages_result = await db.execute(
        select(PipelineStage).where(
            PipelineStage.user_id == current_user.id
        ).order_by(PipelineStage.order)
    )
    stages = stages_result.scalars().all()

    data = []
    for stage in stages:
        count = await db.scalar(
            select(func.count(Deal.id)).where(
                Deal.user_id == current_user.id,
                Deal.stage_id == stage.id,
            )
        )
        amount = await db.scalar(
            select(func.sum(Deal.amount)).where(
                Deal.user_id == current_user.id,
                Deal.stage_id == stage.id,
            )
        ) or 0
        data.append({
            "stage": stage.name,
            "color": stage.color,
            "count": count,
            "amount": float(amount),
        })

    return {"chart_data": data}
