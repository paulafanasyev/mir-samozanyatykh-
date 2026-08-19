"""
API бухгалтерии — Мир Самозанятых v8.1
Доходы, расходы, транзакции, налоговые отчёты, вычеты
АНО ЦПС ИНН 9724016805
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.core.auth import get_current_user, get_current_user_optional
from app.core.rate_limiter import rate_limit
from app.models import User, Transaction, TaxReport, TaxDeduction, BudgetCategory, Invoice

router = APIRouter(prefix="/api/accounting", tags=["accounting"])

MONEY_QUANT = Decimal("0.01")

def money(value: Decimal) -> Decimal:
    """Нормализует денежные значения до 2 знаков без float-арифметики."""
    return Decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

def validate_period(start: datetime, end: datetime) -> None:
    if end <= start:
        raise HTTPException(status_code=422, detail="period_end должен быть позже period_start")



# ============ SCHEMAS ============

class TransactionCreate(BaseModel):
    transaction_type: str = Field(..., pattern="^(income|expense)$")
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="RUB", max_length=3)
    description: Optional[str] = None
    counterparty: Optional[str] = Field(None, max_length=255)
    counterparty_inn: Optional[str] = Field(None, max_length=20)
    counterparty_type: Optional[str] = Field(None, pattern="^(individual|legal_entity|unknown)$")
    transaction_date: datetime
    document_type: Optional[str] = Field(None, max_length=50)
    document_number: Optional[str] = Field(None, max_length=100)
    tax_deductible: bool = False
    source: str = Field(default="manual")


class TransactionUpdate(BaseModel):
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = None
    counterparty: Optional[str] = Field(None, max_length=255)
    transaction_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(pending|confirmed|cancelled)$")
    tax_deductible: Optional[bool] = None


class TransactionOut(BaseModel):
    id: int
    transaction_type: str
    category: str
    subcategory: Optional[str]
    amount: Decimal
    currency: str
    description: Optional[str]
    counterparty: Optional[str]
    counterparty_type: Optional[str]
    transaction_date: datetime
    status: str
    tax_deductible: bool
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaxReportCreate(BaseModel):
    report_type: str = Field(..., pattern="^(npd_quarterly|ndfl_annual|usn)$")
    period_start: datetime
    period_end: datetime


class TaxReportOut(BaseModel):
    id: int
    report_type: str
    period_start: datetime
    period_end: datetime
    total_income: Decimal
    total_expense: Decimal
    taxable_amount: Decimal
    tax_amount: Decimal
    tax_rate_applied: Optional[Decimal]
    deduction_total: Decimal
    status: str
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaxDeductionCreate(BaseModel):
    deduction_type: str = Field(..., pattern="^(professional|social|property|investment)$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    max_amount: Optional[Decimal] = None
    year: int = Field(..., ge=2020, le=2030)


class TaxDeductionOut(BaseModel):
    id: int
    deduction_type: str
    name: str
    amount: Decimal
    max_amount: Optional[Decimal]
    status: str
    year: int
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category_type: str = Field(..., pattern="^(income|expense)$")
    color: Optional[str] = Field(default="#1976D2", max_length=7)
    icon: Optional[str] = Field(default="dollar-sign", max_length=50)
    monthly_limit: Optional[Decimal] = None


class DashboardStats(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_profit: Decimal
    tax_estimate: Decimal
    pending_invoices: int
    overdue_invoices: int
    transactions_count: int
    top_expense_categories: List[dict]
    monthly_trend: List[dict]


# ============ TRANSACTIONS ============

@router.get("/transactions", response_model=List[TransactionOut])
@rate_limit("60/minute")
async def list_transactions(
    request: Request,
    transaction_type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = Query(None, pattern="^(pending|confirmed|cancelled)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список транзакций с фильтрацией"""
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    if category:
        query = query.where(Transaction.category.ilike(f"%{category}%"))
    if start_date:
        query = query.where(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.where(Transaction.transaction_date <= end_date)
    if status:
        query = query.where(Transaction.status == status)

    query = query.order_by(Transaction.transaction_date.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/transactions", response_model=TransactionOut, status_code=201)
@rate_limit("30/minute")
async def create_transaction(
    request: Request,
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создание транзакции (доход или расход). Налоговый контур хранит только RUB."""
    if data.currency.upper() != "RUB":
        raise HTTPException(status_code=422, detail="Для бухгалтерского и налогового контура поддерживается только RUB")
    amount = money(data.amount)
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type=data.transaction_type,
        category=data.category,
        subcategory=data.subcategory,
        amount=amount,
        currency=data.currency,
        description=data.description,
        counterparty=data.counterparty,
        counterparty_inn=data.counterparty_inn,
        counterparty_type=data.counterparty_type,
        transaction_date=data.transaction_date,
        document_type=data.document_type,
        document_number=data.document_number,
        tax_deductible=data.tax_deductible,
        source=data.source,
        status="confirmed",
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    logger.info(f"Transaction created: {data.transaction_type} {data.amount} by user {current_user.id}")
    return transaction


@router.get("/transactions/{transaction_id}", response_model=TransactionOut)
@rate_limit("60/minute")
async def get_transaction(
    request: Request,
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получение транзакции по ID"""
    result = await db.execute(
        select(Transaction).where(
            and_(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    return transaction


@router.put("/transactions/{transaction_id}", response_model=TransactionOut)
@rate_limit("30/minute")
async def update_transaction(
    request: Request,
    transaction_id: int,
    data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновление транзакции"""
    result = await db.execute(
        select(Transaction).where(
            and_(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)

    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=204)
@rate_limit("30/minute")
async def delete_transaction(
    request: Request,
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удаление транзакции"""
    result = await db.execute(
        select(Transaction).where(
            and_(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    await db.delete(transaction)
    await db.commit()
    return {"message": "Транзакция удалена"}


# ============ TAX REPORTS ============

@router.get("/tax-reports", response_model=List[TaxReportOut])
@rate_limit("60/minute")
async def list_tax_reports(
    request: Request,
    report_type: Optional[str] = Query(None, pattern="^(npd_quarterly|ndfl_annual|usn)$"),
    status: Optional[str] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список налоговых отчётов"""
    query = select(TaxReport).where(TaxReport.user_id == current_user.id)

    if report_type:
        query = query.where(TaxReport.report_type == report_type)
    if status:
        query = query.where(TaxReport.status == status)
    if year:
        query = query.where(extract("year", TaxReport.period_start) == year)

    query = query.order_by(TaxReport.period_start.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/tax-reports", response_model=TaxReportOut, status_code=201)
@rate_limit("10/minute")
async def create_tax_report(
    request: Request,
    data: TaxReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создание налогового отчёта (автоматический расчёт)."""
    validate_period(data.period_start, data.period_end)
    # Не создаём дубликаты одного и того же отчётного периода.
    existing_result = await db.execute(
        select(TaxReport).where(and_(
            TaxReport.user_id == current_user.id,
            TaxReport.report_type == data.report_type,
            TaxReport.period_start == data.period_start,
            TaxReport.period_end == data.period_end,
        ))
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        return existing
    # Автоматический расчёт на основе транзакций за период
    income_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "income",
                Transaction.status == "confirmed",
                Transaction.transaction_date >= data.period_start,
                Transaction.transaction_date <= data.period_end,
            )
        )
    )
    total_income = income_result.scalar() or Decimal("0")

    expense_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "expense",
                Transaction.status == "confirmed",
                Transaction.transaction_date >= data.period_start,
                Transaction.transaction_date <= data.period_end,
            )
        )
    )
    total_expense = expense_result.scalar() or Decimal("0")

    # Вычеты
    deductions_result = await db.execute(
        select(func.sum(TaxDeduction.amount)).where(
            and_(
                TaxDeduction.user_id == current_user.id,
                TaxDeduction.status == "active",
                TaxDeduction.year == data.period_start.year,
            )
        )
    )
    deduction_total = deductions_result.scalar() or Decimal("0")

    # Расчёт налога. Для НПД расходы не уменьшают налоговую базу.
    if data.report_type == "npd_quarterly":
        # Доходы НПД разделяются по типу заказчика. Неопределённые доходы
        # считаются рискованными и требуют ручной проверки пользователем.
        individual_result = await db.execute(select(func.sum(Transaction.amount)).where(and_(
            Transaction.user_id == current_user.id, Transaction.transaction_type == "income",
            Transaction.status == "confirmed", Transaction.transaction_date >= data.period_start,
            Transaction.transaction_date <= data.period_end,
            or_(Transaction.counterparty_type == "individual", Transaction.counterparty_type.is_(None)),
        )))
        legal_result = await db.execute(select(func.sum(Transaction.amount)).where(and_(
            Transaction.user_id == current_user.id, Transaction.transaction_type == "income",
            Transaction.status == "confirmed", Transaction.transaction_date >= data.period_start,
            Transaction.transaction_date <= data.period_end,
            Transaction.counterparty_type == "legal_entity",
        )))
        individual_income = individual_result.scalar() or Decimal("0")
        legal_income = legal_result.scalar() or Decimal("0")
        tax_amount = money(individual_income * Decimal("0.04") + legal_income * Decimal("0.06"))
        taxable_amount = money(individual_income + legal_income)
        deduction_total = Decimal("0")
        tax_rate = money((tax_amount / taxable_amount * 100) if taxable_amount else Decimal("0")) / 100
    elif data.report_type == "ndfl_annual":
        tax_rate = Decimal("0.13")
        taxable_amount = max(total_income - deduction_total, Decimal("0"))
    else:  # usn
        tax_rate = Decimal("0.06")
        taxable_amount = max(total_income, Decimal("0"))

    taxable_amount = money(taxable_amount)
    if data.report_type != "npd_quarterly":
        tax_amount = money(taxable_amount * tax_rate)
    total_income = money(total_income)
    total_expense = money(total_expense)
    deduction_total = money(deduction_total)

    report = TaxReport(
        user_id=current_user.id,
        report_type=data.report_type,
        period_start=data.period_start,
        period_end=data.period_end,
        total_income=total_income,
        total_expense=total_expense,
        taxable_amount=taxable_amount,
        tax_amount=tax_amount,
        tax_rate_applied=money(tax_rate * 100),
        deduction_total=deduction_total,
        status="draft",
        risk_level="low",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    logger.info(f"Tax report created: {data.report_type} for user {current_user.id}")
    return report


@router.get("/tax-reports/{report_id}", response_model=TaxReportOut)
@rate_limit("60/minute")
async def get_tax_report(
    request: Request,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получение налогового отчёта"""
    result = await db.execute(
        select(TaxReport).where(
            and_(TaxReport.id == report_id, TaxReport.user_id == current_user.id)
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return report


@router.post("/tax-reports/{report_id}/submit")
@rate_limit("5/minute")
async def submit_tax_report(
    request: Request,
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отправка отчёта (пометка как поданный)"""
    result = await db.execute(
        select(TaxReport).where(
            and_(TaxReport.id == report_id, TaxReport.user_id == current_user.id)
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")

    report.status = "submitted"
    report.submitted_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Отчёт помечен как поданный", "report_id": report_id}


# ============ TAX DEDUCTIONS ============

@router.get("/deductions", response_model=List[TaxDeductionOut])
@rate_limit("60/minute")
async def list_deductions(
    request: Request,
    deduction_type: Optional[str] = Query(None, pattern="^(professional|social|property|investment)$"),
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список налоговых вычетов"""
    query = select(TaxDeduction).where(TaxDeduction.user_id == current_user.id)

    if deduction_type:
        query = query.where(TaxDeduction.deduction_type == deduction_type)
    if year:
        query = query.where(TaxDeduction.year == year)

    query = query.order_by(TaxDeduction.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/deductions", response_model=TaxDeductionOut, status_code=201)
@rate_limit("30/minute")
async def create_deduction(
    request: Request,
    data: TaxDeductionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создание налогового вычета"""
    if data.max_amount is not None:
        if data.max_amount <= 0:
            raise HTTPException(status_code=422, detail="max_amount должен быть больше нуля")
        if data.amount > data.max_amount:
            raise HTTPException(status_code=422, detail="Сумма вычета не может превышать максимальный размер")
    deduction = TaxDeduction(
        user_id=current_user.id,
        deduction_type=data.deduction_type,
        name=data.name,
        description=data.description,
        amount=data.amount,
        max_amount=data.max_amount,
        year=data.year,
        status="active",
    )
    db.add(deduction)
    await db.commit()
    await db.refresh(deduction)
    return deduction


@router.delete("/deductions/{deduction_id}", status_code=204)
@rate_limit("30/minute")
async def delete_deduction(
    request: Request,
    deduction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удаление вычета"""
    result = await db.execute(
        select(TaxDeduction).where(
            and_(TaxDeduction.id == deduction_id, TaxDeduction.user_id == current_user.id)
        )
    )
    deduction = result.scalar_one_or_none()
    if not deduction:
        raise HTTPException(status_code=404, detail="Вычет не найден")

    await db.delete(deduction)
    await db.commit()
    return {"message": "Вычет удалён"}


# ============ BUDGET CATEGORIES ============

@router.get("/budget-categories")
@rate_limit("60/minute")
async def list_budget_categories(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список категорий бюджета"""
    result = await db.execute(
        select(BudgetCategory)
        .where(BudgetCategory.user_id == current_user.id)
        .where(BudgetCategory.is_active == True)
        .order_by(BudgetCategory.category_type, BudgetCategory.name)
    )
    return result.scalars().all()


@router.post("/budget-categories", status_code=201)
@rate_limit("30/minute")
async def create_budget_category(
    request: Request,
    data: BudgetCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создание категории бюджета"""
    category = BudgetCategory(
        user_id=current_user.id,
        name=data.name,
        category_type=data.category_type,
        color=data.color,
        icon=data.icon,
        monthly_limit=data.monthly_limit,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


# ============ DASHBOARD ============

@router.get("/dashboard", response_model=DashboardStats)
@rate_limit("30/minute")
async def get_dashboard(
    request: Request,
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Финансовый дашборд"""
    now = datetime.now(timezone.utc)

    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    elif period == "quarter":
        start = now - timedelta(days=90)
    else:
        start = now - timedelta(days=365)

    # Доходы
    income_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "income",
                Transaction.status == "confirmed",
                Transaction.transaction_date >= start,
            )
        )
    )
    total_income = income_result.scalar() or Decimal("0")

    # Расходы
    expense_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "expense",
                Transaction.status == "confirmed",
                Transaction.transaction_date >= start,
            )
        )
    )
    total_expense = expense_result.scalar() or Decimal("0")

    # Налог (оценка для НПД 4%)
    tax_estimate = total_income * Decimal("0.04")

    # Просроченные счета
    overdue_result = await db.execute(
        select(func.count(Invoice.id)).where(
            and_(
                Invoice.user_id == current_user.id,
                Invoice.status == "sent",
                Invoice.due_date < now,
            )
        )
    )
    overdue_invoices = overdue_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Invoice.id)).where(
            and_(
                Invoice.user_id == current_user.id,
                Invoice.status.in_(["draft", "sent", "pending"]),
            )
        )
    )
    pending_invoices = pending_result.scalar() or 0

    transactions_count_result = await db.execute(
        select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
    )
    transactions_count = transactions_count_result.scalar() or 0

    # Топ категорий расходов
    top_expenses_result = await db.execute(
        select(Transaction.category, func.sum(Transaction.amount))
        .where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "expense",
                Transaction.status == "confirmed",
                Transaction.transaction_date >= start,
            )
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    top_expense_categories = [
        {"category": cat, "amount": float(amt)}
        for cat, amt in top_expenses_result.all()
    ]

    # Месячный тренд (последние 6 месяцев)
    monthly_trend = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)

        inc = await db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.user_id == current_user.id,
                    Transaction.transaction_type == "income",
                    Transaction.status == "confirmed",
                    Transaction.transaction_date >= month_start,
                    Transaction.transaction_date < month_end,
                )
            )
        )
        exp = await db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.user_id == current_user.id,
                    Transaction.transaction_type == "expense",
                    Transaction.status == "confirmed",
                    Transaction.transaction_date >= month_start,
                    Transaction.transaction_date < month_end,
                )
            )
        )
        monthly_trend.append({
            "month": month_start.strftime("%Y-%m"),
            "income": float(inc.scalar() or 0),
            "expense": float(exp.scalar() or 0),
        })

    return DashboardStats(
        total_income=total_income,
        total_expense=total_expense,
        net_profit=total_income - total_expense,
        tax_estimate=tax_estimate,
        pending_invoices=pending_invoices,
        overdue_invoices=overdue_invoices,
        transactions_count=transactions_count,
        top_expense_categories=top_expense_categories,
        monthly_trend=monthly_trend,
    )


# ============ CATEGORIES LIST ============

@router.get("/categories")
@rate_limit("60/minute")
async def get_categories(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Стандартные категории доходов и расходов"""
    return {
        "income": [
            {"id": "salary", "name": "Зарплата / Гонорар", "icon": "briefcase"},
            {"id": "service", "name": "Услуги", "icon": "tool"},
            {"id": "product", "name": "Продажа товаров", "icon": "package"},
            {"id": "rent", "name": "Аренда", "icon": "home"},
            {"id": "dividend", "name": "Дивиденды", "icon": "trending-up"},
            {"id": "interest", "name": "Проценты", "icon": "percent"},
            {"id": "gift", "name": "Подарки", "icon": "gift"},
            {"id": "other_income", "name": "Прочие доходы", "icon": "plus-circle"},
        ],
        "expense": [
            {"id": "rent", "name": "Аренда помещения", "icon": "home"},
            {"id": "utilities", "name": "Коммунальные услуги", "icon": "zap"},
            {"id": "internet", "name": "Интернет и связь", "icon": "wifi"},
            {"id": "software", "name": "ПО и подписки", "icon": "monitor"},
            {"id": "equipment", "name": "Оборудование", "icon": "cpu"},
            {"id": "marketing", "name": "Реклама и маркетинг", "icon": "speaker"},
            {"id": "transport", "name": "Транспорт", "icon": "truck"},
            {"id": "food", "name": "Питание", "icon": "coffee"},
            {"id": "education", "name": "Обучение", "icon": "book"},
            {"id": "health", "name": "Медицина", "icon": "heart"},
            {"id": "tax", "name": "Налоги", "icon": "file-text"},
            {"id": "other_expense", "name": "Прочие расходы", "icon": "minus-circle"},
        ],
    }
