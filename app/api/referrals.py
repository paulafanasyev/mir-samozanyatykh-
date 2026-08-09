"""
API реферальной системы v7.6
Приглашения, бонусы, уровни, начисления
АНО ЦПС ИНН 9724016805
"""

import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.core.logging import log_audit
from app.core.config import settings
from app.models import User, Referral, Notification

router = APIRouter(prefix="/api/referrals", tags=["referrals"])


# ============ CONFIG ============

REFERRAL_REWARDS = {
    "registration": Decimal("50"),    # 50 руб за регистрацию реферала
    "first_payment": Decimal("200"),  # 200 руб за первую оплату
    "tier_upgrade": Decimal("500"),   # 500 руб за апгрейд тарифа
}

REFERRAL_LEVELS = [
    {"name": "Новичок", "min": 0, "bonus_pct": 5},
    {"name": "Активный", "min": 5, "bonus_pct": 10},
    {"name": "Партнёр", "min": 15, "bonus_pct": 15},
    {"name": "Амбассадор", "min": 50, "bonus_pct": 25},
]


def generate_referral_code() -> str:
    """Генерация уникального реферального кода"""
    return secrets.token_urlsafe(6).upper().replace("-", "").replace("_", "")[:8]


def get_referral_level(count: int) -> dict:
    """Определение уровня реферала по количеству приглашённых"""
    for level in reversed(REFERRAL_LEVELS):
        if count >= level["min"]:
            return level
    return REFERRAL_LEVELS[0]


# ============ SCHEMAS ============

class ReferralOut(BaseModel):
    id: int
    referred_email: str
    referred_name: Optional[str]
    status: str
    reward_amount: float
    reward_paid: bool
    created_at: datetime
    converted_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReferralStats(BaseModel):
    referral_code: str
    referral_link: str
    total_referrals: int
    active_referrals: int
    paid_referrals: int
    total_earnings: float
    pending_earnings: float
    level: str
    level_bonus_pct: int
    next_level: Optional[str]
    next_level_min: Optional[int]


class ApplyReferralCode(BaseModel):
    code: str


# ============ ENDPOINTS ============

@router.get("/me")
async def my_referral_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Информация о моей реферальной программе"""
    # Генерация кода если нет
    if not current_user.referral_code:
        current_user.referral_code = generate_referral_code()
        await db.commit()
        await db.refresh(current_user)

    # Статистика
    total = await db.scalar(
        select(func.count(Referral.id)).where(Referral.referrer_id == current_user.id)
    )
    active = await db.scalar(
        select(func.count(Referral.id)).where(
            Referral.referrer_id == current_user.id,
            Referral.status == "active",
        )
    )
    paid = await db.scalar(
        select(func.count(Referral.id)).where(
            Referral.referrer_id == current_user.id,
            Referral.reward_paid == True,
        )
    )
    earnings = await db.scalar(
        select(func.sum(Referral.reward_amount)).where(
            Referral.referrer_id == current_user.id,
        )
    ) or Decimal("0")
    pending = await db.scalar(
        select(func.sum(Referral.reward_amount)).where(
            Referral.referrer_id == current_user.id,
            Referral.reward_paid == False,
        )
    ) or Decimal("0")

    level = get_referral_level(total)
    next_level = None
    next_level_min = None
    for l in REFERRAL_LEVELS:
        if l["min"] > total:
            next_level = l["name"]
            next_level_min = l["min"]
            break

    await log_audit(
        action="referral_info_viewed",
        user_id=current_user.id,
        ip_address=request.client.host,
    )

    return ReferralStats(
        referral_code=current_user.referral_code,
        referral_link=f"https://{settings.DOMAIN}/register?ref={current_user.referral_code}",
        total_referrals=total,
        active_referrals=active,
        paid_referrals=paid,
        total_earnings=float(earnings),
        pending_earnings=float(pending),
        level=level["name"],
        level_bonus_pct=level["bonus_pct"],
        next_level=next_level,
        next_level_min=next_level_min,
    )


@router.get("/my-referrals", response_model=List[ReferralOut])
async def list_my_referrals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список моих рефералов"""
    result = await db.execute(
        select(Referral, User)
        .join(User, Referral.referred_id == User.id)
        .where(Referral.referrer_id == current_user.id)
        .order_by(Referral.created_at.desc())
    )
    rows = result.all()
    return [
        ReferralOut(
            id=ref.id,
            referred_email=user.email,
            referred_name=user.full_name,
            status=ref.status,
            reward_amount=float(ref.reward_amount),
            reward_paid=ref.reward_paid,
            created_at=ref.created_at,
            converted_at=ref.converted_at,
        )
        for ref, user in rows
    ]


@router.post("/apply", status_code=status.HTTP_200_OK)
async def apply_referral_code(
    data: ApplyReferralCode,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Применить реферальный код (после регистрации)"""
    # Нельзя быть своим рефералом
    if current_user.referral_code == data.code:
        raise HTTPException(status_code=400, detail="Нельзя использовать свой код")

    # Проверка что пользователь ещё не привязан
    if current_user.referred_by:
        raise HTTPException(status_code=400, detail="Вы уже использовали реферальный код")

    # Поиск реферера
    result = await db.execute(
        select(User).where(User.referral_code == data.code.upper().strip())
    )
    referrer = result.scalar_one_or_none()
    if not referrer:
        raise HTTPException(status_code=404, detail="Реферальный код не найден")

    # Нельзя быть рефералом того, кого ты пригласил
    existing = await db.scalar(
        select(func.count(Referral.id)).where(Referral.referrer_id == current_user.id)
    )
    if existing > 0:
        raise HTTPException(status_code=400, detail="Вы уже приглашали пользователей")

    # Создание записи реферала
    reward = REFERRAL_REWARDS["registration"]
    level = get_referral_level(referrer.referral_count or 0)
    bonus = reward * Decimal(level["bonus_pct"]) / Decimal("100")
    total_reward = reward + bonus

    referral = Referral(
        referrer_id=referrer.id,
        referred_id=current_user.id,
        status="registered",
        reward_amount=total_reward,
    )
    db.add(referral)

    # Обновление статистики реферера
    current_user.referred_by = referrer.id
    referrer.referral_count = (referrer.referral_count or 0) + 1
    referrer.points = (referrer.points or 0) + 50

    await db.commit()

    # Уведомление рефереру
    db.add(Notification(
        user_id=referrer.id,
        title="Новый реферал!",
        body=f"{current_user.full_name or current_user.email} зарегистрировался по вашей ссылке. +{float(total_reward)} руб.",
        notification_type="success",
    ))
    await db.commit()

    await log_audit(
        action="referral_applied",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Applied code {data.code}, referrer={referrer.id}",
    )

    return {
        "message": "Реферальный код применён",
        "referrer": referrer.full_name or referrer.email,
        "reward": float(total_reward),
        "level_bonus": level["bonus_pct"],
    }


@router.post("/reward/{referral_id}")
async def mark_referral_reward(
    referral_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отметить реферала как активного (начислить награду) — вызывается при оплате"""
    result = await db.execute(
        select(Referral).where(
            Referral.id == referral_id,
            Referral.referrer_id == current_user.id,
        )
    )
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Реферал не найден")

    if referral.status == "paid":
        raise HTTPException(status_code=400, detail="Награда уже начислена")

    # Дополнительная награда за активность
    extra_reward = REFERRAL_REWARDS["first_payment"]
    referral.status = "active"
    referral.reward_amount = referral.reward_amount + extra_reward
    referral.converted_at = datetime.now(timezone.utc)

    # Обновление earnings реферера
    referrer_result = await db.execute(select(User).where(User.id == current_user.id))
    referrer = referrer_result.scalar_one()
    referrer.referral_earnings = (referrer.referral_earnings or Decimal("0")) + extra_reward
    referrer.points = (referrer.points or 0) + 100

    await db.commit()

    # Уведомление
    db.add(Notification(
        user_id=referrer.id,
        title="Реферал стал активным!",
        body=f"Ваш реферал совершил первую оплату. +{float(extra_reward)} руб. бонуса.",
        notification_type="success",
    ))
    await db.commit()

    await log_audit(
        action="referral_rewarded",
        user_id=current_user.id,
        ip_address=request.client.host,
        details=f"Referral {referral_id} marked active, reward={extra_reward}",
    )

    return {
        "message": "Реферал отмечен как активный",
        "bonus": float(extra_reward),
        "total_reward": float(referral.reward_amount),
    }


@router.get("/leaderboard")
async def referral_leaderboard(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Топ рефереров платформы"""
    result = await db.execute(
        select(
            User.id,
            User.full_name,
            User.email,
            User.referral_count,
            User.referral_earnings,
            User.points,
        )
        .where(User.referral_count > 0)
        .order_by(User.referral_count.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "rank": i + 1,
            "name": row.full_name or row.email,
            "referrals": row.referral_count,
            "earnings": float(row.referral_earnings or 0),
            "points": row.points,
            "level": get_referral_level(row.referral_count or 0)["name"],
        }
        for i, row in enumerate(rows)
    ]


@router.get("/levels")
async def referral_levels():
    """Информация об уровнях реферальной программы"""
    return {
        "levels": REFERRAL_LEVELS,
        "rewards": {k: float(v) for k, v in REFERRAL_REWARDS.items()},
    }
