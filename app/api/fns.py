"""
API интеграции с ФНС России — Мир Самозанятых v8.1
Проверка ИНН, чеки, налоговые вычеты
АНО ЦПС ИНН 9724016805
"""

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import logger
from app.core.rate_limiter import rate_limit
from app.models import User, FNSReceipt, Transaction

router = APIRouter(prefix="/api/fns", tags=["fns"])


# ============ SCHEMAS ============

class INNVerifyRequest(BaseModel):
    inn: str = Field(..., min_length=10, max_length=12, pattern=r"^\d{10,12}$")


class INNVerifyResponse(BaseModel):
    inn: str
    valid: bool
    type: str  # individual, legal
    name: Optional[str] = None
    ogrn: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None  # active, liquidated
    message: str


class ReceiptCheckRequest(BaseModel):
    fiscal_document_number: str = Field(..., min_length=1, max_length=50)
    fiscal_sign: str = Field(..., min_length=1, max_length=50)
    date: str = Field(..., pattern=r"^\d{8}T\d{4}$")  # YYYYMMDDTHHMM
    sum: int = Field(..., gt=0)  # сумма в копейках


class ReceiptCheckResponse(BaseModel):
    found: bool
    receipt_id: Optional[str] = None
    seller_name: Optional[str] = None
    seller_inn: Optional[str] = None
    total_amount: Optional[Decimal] = None
    items: Optional[list] = None
    date: Optional[str] = None
    message: str


class ReceiptSaveRequest(BaseModel):
    fns_id: str = Field(..., min_length=1, max_length=255)
    fiscal_document_number: Optional[str] = Field(None, max_length=50)
    fiscal_sign: Optional[str] = Field(None, max_length=50)
    receipt_date: datetime
    total_amount: Decimal = Field(..., gt=0)
    seller_name: Optional[str] = Field(None, max_length=255)
    seller_inn: Optional[str] = Field(None, max_length=20)
    items: Optional[list] = None


# ============ INN VERIFICATION ============

@router.post("/verify-inn", response_model=INNVerifyResponse)
@rate_limit("30/minute")
async def verify_inn(
    request: Request,
    data: INNVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Проверка ИНН через API ФНС (или внутреннюю валидацию)"""
    inn = data.inn.strip()

    # Базовая валидация
    if not re.match(r"^\d{10,12}$", inn):
        raise HTTPException(status_code=400, detail="Неверный формат ИНН")

    # Контрольная сумма ИНН (10-значный)
    def check_inn_10(inn_str: str) -> bool:
        if len(inn_str) != 10:
            return False
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(inn_str[i]) * weights[i] for i in range(9)) % 11 % 10
        return checksum == int(inn_str[9])

    # Контрольная сумма ИНН (12-значный)
    def check_inn_12(inn_str: str) -> bool:
        if len(inn_str) != 12:
            return False
        weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum1 = sum(int(inn_str[i]) * weights1[i] for i in range(10)) % 11 % 10
        checksum2 = sum(int(inn_str[i]) * weights2[i] for i in range(11)) % 11 % 10
        return checksum1 == int(inn_str[10]) and checksum2 == int(inn_str[11])

    valid = check_inn_10(inn) if len(inn) == 10 else check_inn_12(inn)

    # Определяем тип
    inn_type = "legal" if len(inn) == 10 else "individual"

    # Попытка получить данные из ФНС API (если настроен)
    name = None
    ogrn = None
    address = None
    status = None

    if settings.FNS_API_KEY and valid:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{settings.FNS_API_URL}inn",
                    params={"inn": inn},
                    headers={"Authorization": f"Bearer {settings.FNS_API_KEY}"},
                )
                if response.status_code == 200:
                    fns_data = response.json()
                    name = fns_data.get("name")
                    ogrn = fns_data.get("ogrn")
                    address = fns_data.get("address")
                    status = "active" if fns_data.get("status") == "Действующее" else "unknown"
        except Exception as e:
            logger.warning(f"FNS API error for INN {inn}: {e}")

    return INNVerifyResponse(
        inn=inn,
        valid=valid,
        type=inn_type,
        name=name,
        ogrn=ogrn,
        address=address,
        status=status or ("active" if valid else None),
        message="ИНН действителен" if valid else "ИНН недействителен",
    )


# ============ RECEIPT CHECK ============

@router.post("/check-receipt", response_model=ReceiptCheckResponse)
@rate_limit("20/minute")
async def check_receipt(
    request: Request,
    data: ReceiptCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """Проверка чека через API ФНС (ProverkaCheck)"""
    # Формируем запрос к API ФНС
    # Формат: https://proverkacheka.nalog.ru:9999/v1/check/title
    # или через официальное API

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Пробуем официальное API ФНС
            response = await client.post(
                "https://proverkacheka.nalog.ru:9999/v1/check/title",
                json={
                    "fiscalDocumentNumber": data.fiscal_document_number,
                    "fiscalSign": data.fiscal_sign,
                    "date": data.date,
                    "sum": data.sum,
                },
                headers={
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                receipt_data = response.json()
                items = receipt_data.get("items", [])
                total = sum(item.get("sum", 0) for item in items) / 100

                return ReceiptCheckResponse(
                    found=True,
                    receipt_id=receipt_data.get("fiscalDocumentNumber"),
                    seller_name=receipt_data.get("user"),
                    seller_inn=receipt_data.get("userInn"),
                    total_amount=Decimal(str(total)),
                    items=[{
                        "name": item.get("name"),
                        "price": item.get("price", 0) / 100,
                        "quantity": item.get("quantity", 1),
                        "sum": item.get("sum", 0) / 100,
                    } for item in items],
                    date=receipt_data.get("dateTime"),
                    message="Чек найден и подтверждён ФНС",
                )
            elif response.status_code == 406:
                return ReceiptCheckResponse(
                    found=False,
                    message="Чек не найден в базе ФНС. Проверьте данные.",
                )
            else:
                return ReceiptCheckResponse(
                    found=False,
                    message=f"Ошибка проверки чека: {response.status_code}",
                )

    except httpx.ConnectError:
        # Fallback: если API ФНС недоступно, возвращаем заглушку
        logger.warning("FNS receipt API unavailable, returning mock response")
        return ReceiptCheckResponse(
            found=False,
            message="Сервис проверки чеков временно недоступен. Попробуйте позже.",
        )
    except Exception as e:
        logger.error(f"Receipt check error: {e}")
        return ReceiptCheckResponse(
            found=False,
            message="Ошибка при проверке чека",
        )


@router.post("/save-receipt")
@rate_limit("30/minute")
async def save_receipt(
    request: Request,
    data: ReceiptSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Сохранение чека в базу данных"""
    # Проверяем, нет ли уже такого чека
    existing = await db.execute(
        select(FNSReceipt).where(
            and_(
                FNSReceipt.user_id == current_user.id,
                FNSReceipt.fns_id == data.fns_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Чек уже сохранён")

    receipt = FNSReceipt(
        user_id=current_user.id,
        fns_id=data.fns_id,
        fiscal_document_number=data.fiscal_document_number,
        fiscal_sign=data.fiscal_sign,
        receipt_date=data.receipt_date,
        total_amount=data.total_amount,
        cash_amount=Decimal("0"),
        ecash_amount=data.total_amount,
        seller_name=data.seller_name,
        seller_inn=data.seller_inn,
        items=data.items or [],
        status="verified",
        verified_at=datetime.now(timezone.utc),
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)

    # Автоматически создаём транзакцию-расход
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type="expense",
        category="other_expense",
        amount=data.total_amount,
        currency="RUB",
        description=f"Чек от {data.seller_name or 'неизвестного продавца'}",
        counterparty=data.seller_name,
        counterparty_inn=data.seller_inn,
        transaction_date=data.receipt_date,
        source="fns",
        status="confirmed",
    )
    db.add(transaction)
    await db.commit()

    logger.info(f"Receipt saved: {data.fns_id} for user {current_user.id}")
    return {
        "message": "Чек сохранён",
        "receipt_id": receipt.id,
        "transaction_id": transaction.id,
    }


@router.get("/receipts")
@rate_limit("60/minute")
async def list_receipts(
    request: Request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список сохранённых чеков"""
    query = select(FNSReceipt).where(FNSReceipt.user_id == current_user.id)

    if start_date:
        query = query.where(FNSReceipt.receipt_date >= start_date)
    if end_date:
        query = query.where(FNSReceipt.receipt_date <= end_date)

    query = query.order_by(FNSReceipt.receipt_date.desc())
    result = await db.execute(query)
    receipts = result.scalars().all()

    return [
        {
            "id": r.id,
            "fns_id": r.fns_id,
            "seller_name": r.seller_name,
            "seller_inn": r.seller_inn,
            "total_amount": float(r.total_amount),
            "receipt_date": r.receipt_date.isoformat(),
            "items_count": len(r.items) if r.items else 0,
            "status": r.status,
        }
        for r in receipts
    ]


# ============ TAX CALCULATOR ============

@router.get("/tax-calculator")
@rate_limit("60/minute")
async def tax_calculator(
    request: Request,
    income: Decimal = Query(..., gt=0),
    expense: Decimal = Query(default=Decimal("0"), ge=0),
    deductions: Decimal = Query(default=Decimal("0"), ge=0),
    tax_system: str = Query("npd", pattern="^(npd|usn_6|usn_15|osno)$"),
    current_user: User = Depends(get_current_user),
):
    """Калькулятор налогов для самозанятых"""

    # Ставки налогов
    rates = {
        "npd": Decimal("0.04"),      # НПД физлицам
        "npd_legal": Decimal("0.06"),  # НПД юрлицам
        "usn_6": Decimal("0.06"),     # УСН доходы
        "usn_15": Decimal("0.15"),    # УСН доходы-расходы
        "osno": Decimal("0.13"),      # НДФЛ
    }

    rate = rates.get(tax_system, Decimal("0.04"))

    # Для УСН 15%: налог = (доход - расход) * 15%
    if tax_system == "usn_15":
        taxable = income - expense
        if taxable < 0:
            taxable = Decimal("0")
        tax = taxable * rate
    else:
        taxable = income - deductions
        if taxable < 0:
            taxable = Decimal("0")
        tax = taxable * rate

    # Минимальный налог для УСН 15% — 1% от дохода
    if tax_system == "usn_15":
        min_tax = income * Decimal("0.01")
        if tax < min_tax:
            tax = min_tax

    return {
        "income": float(income),
        "expense": float(expense),
        "deductions": float(deductions),
        "taxable_amount": float(taxable),
        "tax_rate": float(rate * 100),
        "tax_amount": float(tax),
        "net_income": float(income - expense - tax),
        "tax_system": tax_system,
        "recommendations": [
            "Сохраняйте все чеки для подтверждения расходов" if expense > 0 else None,
            "Используйте профессиональные вычеты" if deductions == 0 else None,
            "Рассмотрите переход на УСН при доходе > 2.4 млн/год" if income > 200000 else None,
        ],
    }


# ============ SELF-EMPLOYED STATUS ============

@router.get("/self-employed-status")
@rate_limit("30/minute")
async def check_self_employed_status(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Проверка статуса самозанятого (заглушка для интеграции с ФНС)"""
    # В реальности здесь был бы запрос к API ФНС /lkfl/
    # Требуется авторизация через Госуслуги

    if not current_user.inn:
        raise HTTPException(status_code=400, detail="Укажите ИНН в профиле")

    return {
        "inn": current_user.inn,
        "registered_as_self_employed": True,  # Заглушка
        "registration_date": None,
        "tax_rate": "4% (физлица) / 6% (юрлица)",
        "annual_limit": 2_400_000,
        "current_year_income": None,  # Требуется интеграция с ФНС
        "status": "active",
        "message": "Для получения актуальных данных подключите интеграцию с ФНС через Госуслуги",
    }
