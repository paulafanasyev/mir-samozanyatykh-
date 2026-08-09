"""
API интеграции с банками — Мир Самозанятых v8.3
Тинькофф API, Сбер, автоимпорт транзакций
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

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
from app.models import User, Transaction

router = APIRouter(prefix="/api/bank", tags=["bank"])


# ============ SCHEMAS ============

class BankConnectionCreate(BaseModel):
    bank_name: str = Field(..., pattern="^(tinkoff|sber|vtb|raiff|alfa)$")
    api_token: str = Field(..., min_length=10)
    account_number: Optional[str] = Field(None, max_length=50)


class BankConnectionOut(BaseModel):
    id: int
    bank_name: str
    account_number: Optional[str]
    is_active: bool
    last_sync_at: Optional[datetime]
    created_at: datetime


class BankTransactionImport(BaseModel):
    transaction_id: str
    date: datetime
    amount: Decimal
    currency: str = "RUB"
    description: str
    counterparty: Optional[str]
    counterparty_inn: Optional[str]
    operation_type: str  # DEBIT (expense) or CREDIT (income)


class SyncResult(BaseModel):
    imported: int
    skipped: int
    errors: int
    details: List[dict]


# ============ TINKOFF API ============

class TinkoffAPI:
    """Клиент для Тинькофф API"""
    BASE_URL = "https://business.tinkoff.ru/openapi/api/v1"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def get_accounts(self):
        """Получить список счетов"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.BASE_URL}/bank-accounts",
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=502, detail=f"Tinkoff API error: {response.status_code}")

    async def get_operations(self, account_number: str, from_date: datetime, to_date: datetime):
        """Получить операции по счёту"""
        params = {
            "accountNumber": account_number,
            "from": from_date.isoformat(),
            "till": to_date.isoformat(),
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.BASE_URL}/bank-statement",
                headers=self.headers,
                params=params,
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=502, detail=f"Tinkoff API error: {response.status_code}")


# ============ BANK CONNECTIONS ============

@router.post("/connect")
@rate_limit("10/minute")
async def connect_bank(
    request: Request,
    data: BankConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Подключение банковского счёта"""
    # Проверяем токен
    if data.bank_name == "tinkoff":
        try:
            tinkoff = TinkoffAPI(data.api_token)
            accounts = await tinkoff.get_accounts()
            logger.info(f"Tinkoff connected for user {current_user.id}, accounts: {len(accounts.get('accounts', []))}")
        except Exception as e:
            logger.error(f"Tinkoff connection failed: {e}")
            raise HTTPException(status_code=400, detail="Неверный токен Тинькофф API")

    # Сохраняем подключение (в реальности — шифруем токен)
    # Здесь заглушка — в проде нужна таблица bank_connections
    return {
        "message": f"Банк {data.bank_name} подключен",
        "bank_name": data.bank_name,
        "account_number": data.account_number,
        "status": "connected",
    }


@router.post("/sync/tinkoff")
@rate_limit("10/minute")
async def sync_tinkoff(
    request: Request,
    account_number: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Синхронизация операций из Тинькофф"""
    # В реальности токен берётся из БД
    token = settings.TINKOFF_API_TOKEN
    if not token:
        raise HTTPException(status_code=400, detail="Тинькофф API не настроен")

    tinkoff = TinkoffAPI(token)
    to_date = datetime.now(timezone.utc)
    from_date = to_date - __import__('datetime').timedelta(days=days)

    try:
        operations = await tinkoff.get_operations(account_number, from_date, to_date)
    except Exception as e:
        logger.error(f"Tinkoff sync error: {e}")
        # Fallback: возвращаем заглушку
        return {
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "details": [],
            "message": "Синхронизация с Тинькофф временно недоступна. Попробуйте позже.",
        }

    imported = 0
    skipped = 0
    errors = 0
    details = []

    for op in operations.get("operations", []):
        try:
            tx_id = op.get("operationId", "")

            # Проверяем, нет ли уже такой транзакции
            existing = await db.execute(
                select(Transaction).where(
                    and_(
                        Transaction.user_id == current_user.id,
                        Transaction.bank_transaction_id == tx_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Определяем тип операции
            amount = Decimal(str(op.get("amount", 0)))
            operation_type = op.get("operationType", "")
            if operation_type == "DEBIT":
                tx_type = "expense"
                amount = abs(amount)
            else:
                tx_type = "income"

            # Определяем категорию по описанию
            description = op.get("paymentPurpose", "")
            category = _categorize_transaction(description)

            transaction = Transaction(
                user_id=current_user.id,
                transaction_type=tx_type,
                category=category,
                amount=amount,
                currency=op.get("currency", "RUB"),
                description=description[:500],
                counterparty=op.get("counterpartyName", ""),
                counterparty_inn=op.get("counterpartyInn", ""),
                transaction_date=datetime.fromisoformat(op.get("executed", "").replace("Z", "+00:00")),
                bank_transaction_id=tx_id,
                source="bank",
                status="confirmed",
            )
            db.add(transaction)
            imported += 1

        except Exception as e:
            errors += 1
            details.append({"operation_id": op.get("operationId"), "error": str(e)})

    await db.commit()

    logger.info(f"Tinkoff sync: {imported} imported, {skipped} skipped, {errors} errors for user {current_user.id}")

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "details": details,
        "period": f"{from_date.date()} - {to_date.date()}",
    }


def _categorize_transaction(description: str) -> str:
    """Автоматическая категоризация транзакции по описанию"""
    desc_lower = description.lower()

    keywords = {
        "software": ["подписка", "subscription", "software", "license", "лицензия", "figma", "notion", "github", "gitlab"],
        "rent": ["аренда", "rent", "офис", "помещение"],
        "internet": ["интернет", "связь", "телефон", "mobile", "beeline", "mts", "megafon"],
        "marketing": ["реклама", "marketing", "ads", "google ads", "яндекс.директ", "facebook"],
        "transport": ["такси", "uber", "yandex taxi", "бензин", "транспорт"],
        "food": ["ресторан", "кафе", "продукты", "еда", "grocery"],
        "education": ["курс", "обучение", "course", "education", "stepik", "coursera"],
        "health": ["медицина", "аптека", "health", "clinic"],
        "equipment": ["компьютер", "ноутбук", "монитор", "оборудование", "hardware"],
        "tax": ["налог", "tax", "ндфл", "усн", "страховые взносы"],
        "salary": ["зарплата", "salary", "аванс", "премия"],
        "service": ["услуги", "консультация", "service", "работы"],
    }

    for category, words in keywords.items():
        for word in words:
            if word in desc_lower:
                return category

    return "other_expense"


# ============ SBER API (заглушка) ============

@router.post("/sync/sber")
@rate_limit("10/minute")
async def sync_sber(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
):
    """Синхронизация операций из Сбера (в разработке)"""
    return {
        "message": "Интеграция со Сбером в разработке",
        "status": "coming_soon",
        "alternative": "Используйте экспорт CSV из СберБизнес и импорт через /api/import/transactions",
    }


# ============ BANK STATUS ============

@router.get("/status")
@rate_limit("30/minute")
async def bank_status(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Статус подключённых банков"""
    return {
        "tinkoff": {
            "connected": bool(settings.TINKOFF_API_TOKEN),
            "last_sync": None,
            "accounts": [],
        },
        "sber": {
            "connected": False,
            "status": "coming_soon",
        },
        "vtb": {
            "connected": False,
            "status": "planned",
        },
    }


# ============ MANUAL IMPORT ============

@router.post("/import/manual")
@rate_limit("10/minute")
async def import_manual_transactions(
    request: Request,
    transactions: List[BankTransactionImport],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ручной импорт транзакций из банка (CSV/Excel)"""
    imported = 0
    skipped = 0

    for tx_data in transactions:
        # Проверяем дубликат
        existing = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.user_id == current_user.id,
                    Transaction.bank_transaction_id == tx_data.transaction_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        tx_type = "expense" if tx_data.operation_type == "DEBIT" else "income"
        category = _categorize_transaction(tx_data.description)

        transaction = Transaction(
            user_id=current_user.id,
            transaction_type=tx_type,
            category=category,
            amount=tx_data.amount,
            currency=tx_data.currency,
            description=tx_data.description[:500],
            counterparty=tx_data.counterparty,
            counterparty_inn=tx_data.counterparty_inn,
            transaction_date=tx_data.date,
            bank_transaction_id=tx_data.transaction_id,
            source="bank",
            status="confirmed",
        )
        db.add(transaction)
        imported += 1

    await db.commit()

    return {
        "imported": imported,
        "skipped": skipped,
        "message": f"Импортировано {imported} транзакций",
    }
