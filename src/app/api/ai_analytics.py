"""
AI Аналитика v7.0
Прогнозирование продаж, рекомендации, скоринг клиентов
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, Deal, Client, PipelineStage
from app.core.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/ai", tags=["ai-analytics"])


@router.get("/forecast/revenue")
async def revenue_forecast(
    months: int = 3,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Прогноз выручки на основе истории сделок"""

    # Исторические данные за последние 6 месяцев
    now = datetime.now(timezone.utc)
    history_start = now - timedelta(days=180)

    # Средняя выручка по месяцам
    monthly_revenue = []
    for i in range(6):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)

        revenue = await db.scalar(
            select(func.sum(Deal.amount)).where(
                Deal.user_id == current_user.id,
                Deal.status == "won",
                Deal.actual_close_date >= month_start,
                Deal.actual_close_date < month_end,
            )
        ) or 0
        monthly_revenue.append(float(revenue))

    monthly_revenue.reverse()

    # Простое линейное прогнозирование
    if len(monthly_revenue) >= 2:
        avg_growth = (monthly_revenue[-1] - monthly_revenue[0]) / max(len(monthly_revenue) - 1, 1)
        forecast = []
        last_value = monthly_revenue[-1]
        for i in range(1, months + 1):
            predicted = max(0, last_value + avg_growth * i)
            forecast.append({
                "month": (now + timedelta(days=30*i)).strftime("%Y-%m"),
                "predicted_revenue": round(predicted, 2),
                "confidence": max(0.3, 1.0 - i * 0.15),  # уверенность падает
            })
    else:
        forecast = [{
            "month": (now + timedelta(days=30*i)).strftime("%Y-%m"),
            "predicted_revenue": monthly_revenue[-1] if monthly_revenue else 0,
            "confidence": 0.5,
        } for i in range(1, months + 1)]

    return {
        "historical": monthly_revenue,
        "forecast": forecast,
        "method": "linear_trend",
    }


@router.get("/scoring/clients")
async def client_scoring(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI-скоринг клиентов по ценности"""

    result = await db.execute(
        select(Client).where(Client.user_id == current_user.id)
    )
    clients = result.scalars().all()

    scored_clients = []
    for client in clients:
        # Подсчёт метрик
        deals_count = await db.scalar(
            select(func.count(Deal.id)).where(
                Deal.client_id == client.id,
            )
        )
        total_revenue = await db.scalar(
            select(func.sum(Deal.amount)).where(
                Deal.client_id == client.id,
                Deal.status == "won",
            )
        ) or 0
        won_deals = await db.scalar(
            select(func.count(Deal.id)).where(
                Deal.client_id == client.id,
                Deal.status == "won",
            )
        )

        # AI-скор (0-100)
        score = min(100, int(
            (won_deals * 15) +  # за закрытые сделки
            (float(total_revenue) / 1000) +  # за выручку
            (deals_count * 5)  # за активность
        ))

        # Категория
        if score >= 80:
            category = "VIP"
        elif score >= 50:
            category = "Ценный"
        elif score >= 20:
            category = "Перспективный"
        else:
            category = "Новый"

        scored_clients.append({
            "client_id": client.id,
            "name": client.name,
            "score": score,
            "category": category,
            "deals_count": deals_count,
            "total_revenue": float(total_revenue),
            "won_deals": won_deals,
        })

    scored_clients.sort(key=lambda x: x["score"], reverse=True)
    return {"clients": scored_clients}


@router.get("/recommendations/deals")
async def deal_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI-рекомендации по сделкам"""

    # Сделки, которые долго не двигаются
    stale_date = datetime.now(timezone.utc) - timedelta(days=14)

    stale_deals = await db.execute(
        select(Deal).where(
            Deal.user_id == current_user.id,
            Deal.status.notin_(["won", "lost"]),
            Deal.updated_at < stale_date,
        )
    )
    stale = stale_deals.scalars().all()

    # Сделки с высокой вероятностью закрытия
    hot_deals = await db.execute(
        select(Deal).where(
            Deal.user_id == current_user.id,
            Deal.probability >= 70,
            Deal.status.notin_(["won", "lost"]),
        ).order_by(Deal.probability.desc()).limit(5)
    )
    hot = hot_deals.scalars().all()

    recommendations = []

    for deal in stale:
        recommendations.append({
            "type": "action_needed",
            "priority": "high",
            "deal_id": deal.id,
            "title": deal.title,
            "message": f"Сделка '{deal.title}' не обновлялась более 14 дней. Нужно связаться с клиентом.",
            "suggested_action": "Отправить follow-up или позвонить",
        })

    for deal in hot:
        recommendations.append({
            "type": "hot_deal",
            "priority": "medium",
            "deal_id": deal.id,
            "title": deal.title,
            "message": f"Высокая вероятность закрытия ({deal.probability}%). Подготовьте коммерческое предложение.",
            "suggested_action": "Отправить КП или провести демо",
        })

    return {
        "recommendations": recommendations,
        "total": len(recommendations),
    }
