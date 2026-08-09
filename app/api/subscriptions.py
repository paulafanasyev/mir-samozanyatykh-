"""
API подписок и тарифов v7.5
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_audit
from app.models import User

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


class UserSubscriptionOut(BaseModel):
    tier: str
    expires_at: Optional[datetime]
    days_left: int
    features: List[str]


@router.get("/tiers")
async def list_tiers():
    """Список доступных тарифов"""
    return {
        "free": {
            "name": "Бесплатный", "price": 0,
            "features": [
                "До 5 клиентов", "До 3 договоров",
                "Базовая статистика", "Email поддержка",
            ],
            "limits": {"clients": 5, "contracts": 3, "products": 10, "invoices_per_month": 10},
        },
        "pro": {
            "name": "Профессиональный", "price": 499,
            "features": [
                "Неограниченные клиенты", "Неограниченные договоры",
                "AI-ассистент Светлана", "PDF генерация", "Приоритетная поддержка",
            ],
            "limits": {"clients": -1, "contracts": -1, "products": -1, "invoices_per_month": -1},
        },
        "business": {
            "name": "Бизнес", "price": 1499,
            "features": [
                "Всё из Профессионального", "ЮKassa интеграция",
                "Массовые рассылки", "CRM воронка", "WebSocket уведомления", "API доступ",
            ],
            "limits": {"clients": -1, "contracts": -1, "products": -1, "invoices_per_month": -1},
        },
        "enterprise": {
            "name": "Корпоративный", "price": 4999,
            "features": [
                "Всё из Бизнеса", "White-label", "Выделенный сервер",
                "SLA 99.9%", "Персональный менеджер",
            ],
            "limits": {"clients": -1, "contracts": -1, "products": -1, "invoices_per_month": -1},
        },
    }


@router.get("/me", response_model=UserSubscriptionOut)
async def my_subscription(current_user: User = Depends(get_current_user)):
    """Текущая подписка пользователя"""
    days_left = 0
    if current_user.subscription_expires:
        days_left = max(0, (current_user.subscription_expires - datetime.now(timezone.utc)).days)

    tiers = await list_tiers()
    tier_data = tiers.get(current_user.tier, tiers["free"])

    return UserSubscriptionOut(
        tier=current_user.tier,
        expires_at=current_user.subscription_expires,
        days_left=days_left,
        features=tier_data.get("features", []),
    )


@router.post("/upgrade")
async def upgrade_subscription(
    tier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Запрос на смену тарифа"""
    if tier not in ["free", "pro", "business", "enterprise"]:
        raise HTTPException(status_code=400, detail="Неверный тариф")

    current_user.subscription_tier = tier
    current_user.subscription_expires = datetime.now(timezone.utc) + timedelta(days=30)
    await db.commit()
    await db.refresh(current_user)

    await log_audit(
        action="subscription_upgraded",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Tier: {tier}",
    )
    return {"message": f"Подписка изменена на {tier}", "expires_at": current_user.subscription_expires}
