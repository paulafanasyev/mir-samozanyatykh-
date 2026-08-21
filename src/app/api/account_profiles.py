"""Account-type registration extensions and partner tariff information."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.api import auth

router = APIRouter(tags=["account profiles"])

ACCOUNT_TYPES = {
    "self_employed": "Самозанятый",
    "individual_entrepreneur": "ИП",
    "company": "ООО / юридическое лицо",
    "employer": "Компания / работодатель",
    "education_center": "Учебный центр",
}

TARIFFS = {
    "self_employed_free": {"name": "Самозанятый — Free", "price": 0, "description": "Бесплатное рабочее пространство. Наш продуктовый лимит — до 2,4 млн ₽ годового оборота, учитываемого внутри платформы; это не заменяет и не изменяет налоговые ограничения НПД.", "limits": {"clients": 25, "contracts_per_month": 10, "invoices_per_month": 30, "storage_mb": 500, "platform_turnover_rub_per_year": 2400000}},
    "self_employed_pro": {"name": "Самозанятый — Pro", "price": 499, "description": "Расширенное рабочее пространство без базовых лимитов: CRM, документы, аналитика и продвижение.", "limits": {"clients": -1, "contracts_per_month": -1, "invoices_per_month": -1, "storage_mb": 5000, "platform_turnover_rub_per_year": -1}},
    "business_start": {"name": "Business Start", "price": 1490, "description": "Для ИП и небольших работодателей: команда, CRM, маркетплейс и документы.", "limits": {"clients": -1, "contracts_per_month": -1, "invoices_per_month": -1, "storage_mb": 10000, "platform_turnover_rub_per_year": -1}},
    "business_pro": {"name": "Business Pro", "price": 2990, "description": "Для компаний: расширенная CRM, роли, аналитика, документы и интеграции.", "limits": {"clients": -1, "contracts_per_month": -1, "invoices_per_month": -1, "storage_mb": 25000, "platform_turnover_rub_per_year": -1}},
    "enterprise": {"name": "Corporate", "price": 7990, "description": "Корпоративный контур с командами, расширенными ролями, API и индивидуальными условиями.", "limits": {"clients": -1, "contracts_per_month": -1, "invoices_per_month": -1, "storage_mb": 100000, "platform_turnover_rub_per_year": -1}},
}


def _profile(user: User) -> dict:
    data = dict(user.branding_settings or {})
    value = data.get("platform_profile", {})
    return value if isinstance(value, dict) else {}


@router.post("/api/auth/register", status_code=201)
async def register_with_account_type(
    request: Request,
    email: str = Form(..., max_length=255),
    password: str = Form(..., max_length=128),
    full_name: str = Form(..., max_length=255),
    phone: Optional[str] = Form(None, max_length=50),
    inn: Optional[str] = Form(None, max_length=20),
    referral_code: Optional[str] = Form(None, max_length=64),
    account_type: str = Form("self_employed"),
    tariff: Optional[str] = Form(None),
    education_partner_agree: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if account_type not in ACCOUNT_TYPES:
        raise HTTPException(status_code=400, detail="Неверный тип аккаунта")
    if account_type == "education_center" and education_partner_agree != "on":
        raise HTTPException(status_code=400, detail="Учебному центру необходимо согласиться с партнёрской офертой")

    default_tariff = "self_employed_free" if account_type == "self_employed" else (
        "business_start" if account_type in {"individual_entrepreneur", "employer", "education_center"} else "enterprise"
    )
    selected_tariff = tariff if tariff in TARIFFS else default_tariff

    result = await auth.register(request=request, email=email, password=password, full_name=full_name, phone=phone, inn=inn, referral_code=referral_code, db=db)
    user = await db.scalar(select(User).where(User.id == int(result["user_id"])))
    if user is None:
        raise HTTPException(status_code=500, detail="Пользователь создан, но профиль не найден")

    profile = dict(user.branding_settings or {})
    profile["platform_profile"] = {
        "account_type": account_type,
        "account_type_label": ACCOUNT_TYPES[account_type],
        "tariff": selected_tariff,
        "tariff_label": TARIFFS[selected_tariff]["name"],
        "education_partner_agree": account_type == "education_center",
    }
    user.branding_settings = profile
    user.subscription_tier = "free" if selected_tariff == "self_employed_free" else ("pro" if selected_tariff == "self_employed_pro" else "business")
    await db.commit()
    return {**result, "account_type": account_type, "account_type_label": ACCOUNT_TYPES[account_type], "tariff": selected_tariff}


@router.get("/api/account/profile")
async def account_profile(current_user: User = Depends(get_current_user)) -> dict:
    profile = _profile(current_user)
    return {"account_type": profile.get("account_type", "self_employed"), "account_type_label": profile.get("account_type_label", "Самозанятый"), "tariff": profile.get("tariff", "self_employed_free"), "tariff_label": profile.get("tariff_label", "Самозанятый — Free"), "education_partner_agree": bool(profile.get("education_partner_agree"))}


@router.get("/api/subscriptions/tiers")
async def public_tariffs() -> dict:
    return TARIFFS


@router.get("/education-partner-offer", response_class=HTMLResponse)
async def education_partner_offer() -> str:
    return """<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Оферта для учебных центров — Мир Самозанятых</title><style>body{font-family:Inter,system-ui,sans-serif;max-width:900px;margin:0 auto;padding:40px 20px;line-height:1.65;color:#172033}h1,h2{color:#c2410c}.card{padding:28px;border:1px solid #e5e7eb;border-radius:20px;background:#fff}</style></head><body><div class='card'><h1>Партнёрская оферта для учебных центров</h1><p><strong>АНО ЦПС «Мир Самозанятых»</strong> предлагает учебным центрам размещение и продвижение образовательных программ на платформе.</p><h2>1. Предмет</h2><p>Партнёр предоставляет сведения о курсах, программах переподготовки и профессионального обучения, а платформа размещает предложения, привлекает потенциальных покупателей и сопровождает продажу.</p><h2>2. Вознаграждение</h2><p>Вознаграждение платформы рассчитывается как комиссия от фактически оплаченной продажи курса. Конкретный процент и порядок расчётов фиксируются в коммерческих условиях партнёрства до начала продаж.</p><h2>3. Ответственность партнёра</h2><p>Учебный центр отвечает за достоверность информации о программе, стоимость, лицензирование и иные обязательные требования к образовательной деятельности.</p><h2>4. Согласие</h2><p>Регистрация в качестве учебного центра означает согласие на рассмотрение партнёрства и условия размещения. Окончательные юридические и коммерческие условия оформляются отдельным договором или приложением.</p><p><strong>Контакт:</strong> it-laboratory@bk.ru</p><p><a href='/register'>Вернуться к регистрации</a></p></div></body></html>"""
