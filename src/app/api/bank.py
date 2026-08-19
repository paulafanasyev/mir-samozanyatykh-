"""
API интеграции с банками — Мир Самозанятых v8.4
Тинькофф API, Сбер, автоимпорт транзакций, шифрование токенов
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.core.auth import get_current_user, get_current_user_optional
from app.core.rate_limiter import rate_limit
from app.models import User, Transaction, BankConnection
from app.services.encryption import get_token_encryption

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
    account_name: Optional[str]
    is_active: bool
    last_sync_at: Optional[datetime]
    last_sync_status: str
    total_synced: int
    created_at: datetime

    class Config:
        from_attributes = True


class BankTransactionImport(BaseModel):
    transaction_id: str
    date: datetime
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    description: str = Field(..., min_length=1, max_length=500)
    counterparty: Optional[str]
    counterparty_inn: Optional[str]
    operation_type: str = Field(..., pattern="^(DEBIT|CREDIT)$")


class SyncResult(BaseModel):
    imported: int
    skipped: int
    errors: int
    details: List[dict]


# ============ TOKEN ENCRYPTION ============

def _encrypt_token(token: str) -> str:
    return get_token_encryption().encrypt(token)


def _decrypt_token(encrypted: str) -> str:
    return get_token_encryption().decrypt(encrypted)


# ============ TINKOFF API ============

class TinkoffAPI:
    """Клиент для Тинькофф OpenAPI v1"""
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
            logger.error(f"Tinkoff get_accounts error: {response.status_code}")
            raise HTTPException(status_code=502, detail="Банковский сервис временно недоступен")

    async def get_operations(self, account_number: str, from_date: datetime, to_date: datetime):
        """Получить операции по счету"""
        params = {
            "accountNumber": account_number,
            "from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "till": to_date.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.BASE_URL}/bank-statement",
                headers=self.headers,
                params=params,
            )
            if response.status_code == 200:
                return response.json()
            logger.error(f"Tinkoff get_operations error: {response.status_code}")
            raise HTTPException(status_code=502, detail="Банковский сервис временно недоступен")


# ============ BANK CONNECTIONS CRUD ============

@router.get("/connections", response_model=List[BankConnectionOut])
async def list_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Список подключенных банков"""
    result = await db.execute(
        select(BankConnection)
        .where(BankConnection.user_id == current_user.id)
        .order_by(desc(BankConnection.created_at))
    )
    return result.scalars().all()


@router.post("/connect", response_model=BankConnectionOut)
@rate_limit("10/minute")
async def connect_bank(
    request: Request,
    data: BankConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Подключение банковского счета с проверкой токена"""
    account_name = None
    if data.bank_name == "tinkoff":
        try:
            tinkoff = TinkoffAPI(data.api_token)
            accounts_data = await tinkoff.get_accounts()
            accounts = accounts_data.get("accounts", [])
            if accounts:
                account_name = accounts[0].get("name", "Счет Тинькофф")
                if not data.account_number:
                    data.account_number = accounts[0].get("accountNumber")
            logger.info(f"Tinkoff connected for user {current_user.id}, accounts: {len(accounts)}")
        except Exception as e:
            logger.error(f"Tinkoff connection failed: {e}")
            raise HTTPException(status_code=400, detail="Неверный токен Тинькофф API")

    existing = await db.execute(
        select(BankConnection).where(
            and_(
                BankConnection.user_id == current_user.id,
                BankConnection.bank_name == data.bank_name,
                BankConnection.account_number == data.account_number,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Этот счет уже подключен")

    connection = BankConnection(
        user_id=current_user.id,
        bank_name=data.bank_name,
        account_number=data.account_number,
        account_name=account_name,
        api_token_encrypted=_encrypt_token(data.api_token),
        is_active=True,
        last_sync_status="pending",
    )
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    return connection


@router.delete("/connections/{connection_id}", status_code=204)
async def disconnect_bank(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отключение банка"""
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.id == connection_id,
            BankConnection.user_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Подключение не найдено")
    await db.delete(connection)
    await db.commit()


@router.get("/transactions")
async def bank_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List imported bank transactions belonging to the current user."""
    from sqlalchemy import func
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(desc(Transaction.transaction_date))
        .offset(offset).limit(page_size)
    )
    items = result.scalars().all()
    return {"items": items, "page": page, "page_size": page_size}


# ============ SYNC ============

@router.post("/sync/{connection_id}", response_model=SyncResult)
@rate_limit("10/minute")
async def sync_bank(
    request: Request,
    connection_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Синхронизация операций из подключенного банка"""
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.id == connection_id,
            BankConnection.user_id == current_user.id,
            BankConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Подключение не найдено")

    try:
        token = _decrypt_token(connection.api_token_encrypted)
    except Exception:
        raise HTTPException(status_code=500, detail="Ошибка дешифрования токена")

    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=days)
    imported = 0
    skipped = 0
    errors = 0
    details = []

    if connection.bank_name == "tinkoff":
        try:
            tinkoff = TinkoffAPI(token)
            operations = await tinkoff.get_operations(
                connection.account_number or "", from_date, to_date
            )
        except Exception as e:
            connection.last_sync_status = "error"
            connection.last_sync_error = "Ошибка синхронизации внешнего банковского API"
            connection.last_sync_at = datetime.now(timezone.utc)
            await db.commit()
            return {"imported": 0, "skipped": 0, "errors": 1, "details": [{"error": "bank_api_unavailable"}]}

        for op in operations.get("operations", []):
            try:
                tx_id = op.get("operationId", "")
                if not tx_id:
                    continue
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

                amount = Decimal(str(op.get("amount", 0)))
                operation_type = op.get("operationType", "")
                tx_type = "expense" if operation_type == "DEBIT" else "income"
                if tx_type == "expense":
                    amount = abs(amount)

                description = op.get("paymentPurpose", "")
                category = _categorize_transaction(description)

                executed = op.get("executed", "")
                tx_date = datetime.now(timezone.utc)
                if executed:
                    try:
                        tx_date = datetime.fromisoformat(executed.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                transaction = Transaction(
                    user_id=current_user.id,
                    transaction_type=tx_type,
                    category=category,
                    amount=amount,
                    currency=op.get("currency", "RUB"),
                    description=description[:500],
                    counterparty=op.get("counterpartyName", "")[:255],
                    counterparty_inn=op.get("counterpartyInn", ""),
                    transaction_date=tx_date,
                    bank_transaction_id=tx_id,
                    source="bank",
                    status="confirmed",
                )
                db.add(transaction)
                imported += 1
            except Exception as e:
                errors += 1
                details.append({"operation_id": op.get("operationId"), "error": "transaction_import_failed"})

    connection.last_sync_at = datetime.now(timezone.utc)
    connection.last_sync_status = "success" if errors == 0 else "partial"
    connection.last_sync_error = None if errors == 0 else f"{errors} errors"
    connection.total_synced += imported
    await db.commit()

    return {"imported": imported, "skipped": skipped, "errors": errors, "details": details}


def _categorize_transaction(description: str) -> str:
    """Автоматическая категоризация транзакции"""
    desc_lower = description.lower()
    # Priority order: education checked before software to avoid "coursera subscription" -> software
    keywords_ordered = [
        ("education", ["курс", "обучение", "course", "education", "stepik", "coursera", "школа", "университет"]),
        ("software", ["подписка", "subscription", "software", "license", "лицензия", "figma", "notion", "github", "gitlab", "slack", "zoom"]),
        ("rent", ["аренда", "rent", "офис", "помещение", "коворкинг"]),
        ("internet", ["интернет", "связь", "телефон", "mobile", "beeline", "mts", "megafon", "tele2"]),
        ("marketing", ["реклама", "marketing", "ads", "google ads", "яндекс.директ", "facebook", "реклам", "таргет"]),
        ("transport", ["такси", "uber", "yandex taxi", "бензин", "транспорт"]),
        ("food", ["ресторан", "кафе", "продукты", "еда", "grocery"]),
        ("health", ["медицина", "аптека", "health", "clinic", "больница"]),
        ("equipment", ["компьютер", "ноутбук", "монитор", "оборудование", "hardware"]),
        ("tax", ["налог", "tax", "ндфл", "усн", "страховые взносы", "пенсионный фонд"]),
        ("salary", ["зарплата", "salary", "аванс", "премия"]),
        ("service", ["услуги", "консультация", "service", "работы"]),
        ("commission", ["комиссия", "commission", "сбор", "fee"]),
    ]
    for category, words in keywords_ordered:
        for word in words:
            if word in desc_lower:
                return category
    return "other_expense"


@router.get("/status")
@rate_limit("30/minute")
async def bank_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Статус подключенных банков"""
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.user_id == current_user.id,
            BankConnection.is_active == True,
        )
    )
    connections = result.scalars().all()

    banks = {
        "tinkoff": {"connected": False, "status": "available" if settings.TINKOFF_API_TOKEN else "not_configured"},
        "sber": {"connected": False, "status": "coming_soon"},
        "vtb": {"connected": False, "status": "planned"},
        "raiff": {"connected": False, "status": "planned"},
        "alfa": {"connected": False, "status": "planned"},
    }

    for conn in connections:
        if conn.bank_name in banks:
            banks[conn.bank_name] = {
                "connected": True,
                "status": conn.last_sync_status,
                "last_sync": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
                "account_name": conn.account_name,
                "total_synced": conn.total_synced,
            }

    if settings.TINKOFF_API_TOKEN:
        banks["tinkoff"]["env_token_configured"] = True

    return banks


@router.post("/import/manual")
@rate_limit("10/minute")
async def import_manual_transactions(
    request: Request,
    transactions: List[BankTransactionImport],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ручной импорт транзакций"""
    imported = 0
    skipped = 0
    for tx_data in transactions:
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
    return {"imported": imported, "skipped": skipped, "message": f"Импортировано {imported} транзакций"}
