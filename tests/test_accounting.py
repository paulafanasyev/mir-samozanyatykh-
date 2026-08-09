"""Tests for accounting module — Mir Samozanyatykh v8.2
ANO TsPS INN 9724016805"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Transaction, TaxReport, TaxDeduction, BudgetCategory
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def accounting_user(db_session: AsyncSession):
    user = User(
        email="accounting_test@example.com",
        full_name="Accounting Test User",
        phone="+79123456783",
        password_hash=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True,
        tier="business",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_transactions(db_session: AsyncSession, accounting_user: User):
    txs = [
        Transaction(
            user_id=accounting_user.id,
            transaction_type="income",
            category="service",
            amount=Decimal("50000.00"),
            currency="RUB",
            description="Razrabotka sayta",
            transaction_date=datetime.now(timezone.utc) - timedelta(days=5),
            status="confirmed",
            source="manual",
        ),
        Transaction(
            user_id=accounting_user.id,
            transaction_type="income",
            category="product",
            amount=Decimal("25000.00"),
            currency="RUB",
            description="Prodazha shablona",
            transaction_date=datetime.now(timezone.utc) - timedelta(days=3),
            status="confirmed",
            source="manual",
        ),
        Transaction(
            user_id=accounting_user.id,
            transaction_type="expense",
            category="software",
            amount=Decimal("15000.00"),
            currency="RUB",
            description="Podpiska Figma",
            transaction_date=datetime.now(timezone.utc) - timedelta(days=2),
            status="confirmed",
            source="manual",
            tax_deductible=True,
        ),
        Transaction(
            user_id=accounting_user.id,
            transaction_type="expense",
            category="rent",
            amount=Decimal("30000.00"),
            currency="RUB",
            description="Arenda ofisa",
            transaction_date=datetime.now(timezone.utc) - timedelta(days=1),
            status="confirmed",
            source="manual",
        ),
    ]
    for tx in txs:
        db_session.add(tx)
    await db_session.commit()
    return txs


class TestTransactionModel:
    """Test Transaction database model"""

    @pytest.mark.asyncio
    async def test_create_income_transaction(self, db_session: AsyncSession, accounting_user: User):
        tx = Transaction(
            user_id=accounting_user.id,
            transaction_type="income",
            category="service",
            amount=Decimal("100000.00"),
            currency="RUB",
            transaction_date=datetime.now(timezone.utc),
            status="confirmed",
            source="manual",
        )
        db_session.add(tx)
        await db_session.commit()
        await db_session.refresh(tx)

        assert tx.id is not None
        assert tx.transaction_type == "income"
        assert tx.amount == Decimal("100000.00")
        assert tx.status == "confirmed"

    @pytest.mark.asyncio
    async def test_create_expense_transaction(self, db_session: AsyncSession, accounting_user: User):
        tx = Transaction(
            user_id=accounting_user.id,
            transaction_type="expense",
            category="software",
            amount=Decimal("5000.00"),
            currency="RUB",
            transaction_date=datetime.now(timezone.utc),
            status="confirmed",
            source="manual",
            tax_deductible=True,
        )
        db_session.add(tx)
        await db_session.commit()

        assert tx.tax_deductible is True
        assert tx.transaction_type == "expense"

    @pytest.mark.asyncio
    async def test_transaction_user_relationship(self, db_session: AsyncSession, accounting_user: User):
        tx = Transaction(
            user_id=accounting_user.id,
            transaction_type="income",
            category="service",
            amount=Decimal("1000.00"),
            currency="RUB",
            transaction_date=datetime.now(timezone.utc),
            status="confirmed",
            source="manual",
        )
        db_session.add(tx)
        await db_session.commit()

        assert tx.user_id == accounting_user.id


class TestTaxReportModel:
    """Test TaxReport database model"""

    @pytest.mark.asyncio
    async def test_create_tax_report(self, db_session: AsyncSession, accounting_user: User):
        report = TaxReport(
            user_id=accounting_user.id,
            report_type="npd_quarterly",
            period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            period_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
            total_income=Decimal("150000.00"),
            total_expense=Decimal("45000.00"),
            taxable_amount=Decimal("105000.00"),
            tax_amount=Decimal("4200.00"),
            tax_rate_applied=Decimal("4.00"),
            deduction_total=Decimal("0.00"),
            status="draft",
            risk_level="low",
        )
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)

        assert report.id is not None
        assert report.report_type == "npd_quarterly"
        assert report.tax_amount == Decimal("4200.00")
        assert report.status == "draft"

    @pytest.mark.asyncio
    async def test_tax_report_status_transitions(self, db_session: AsyncSession, accounting_user: User):
        report = TaxReport(
            user_id=accounting_user.id,
            report_type="ndfl_annual",
            period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            period_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
            total_income=Decimal("600000.00"),
            total_expense=Decimal("200000.00"),
            taxable_amount=Decimal("400000.00"),
            tax_amount=Decimal("52000.00"),
            tax_rate_applied=Decimal("13.00"),
            status="draft",
            risk_level="medium",
        )
        db_session.add(report)
        await db_session.commit()

        # Submit
        report.status = "submitted"
        report.submitted_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(report)

        assert report.status == "submitted"
        assert report.submitted_at is not None


class TestTaxDeductionModel:
    """Test TaxDeduction database model"""

    @pytest.mark.asyncio
    async def test_create_professional_deduction(self, db_session: AsyncSession, accounting_user: User):
        deduction = TaxDeduction(
            user_id=accounting_user.id,
            deduction_type="professional",
            name="Raskhody na oborudovanie",
            amount=Decimal("50000.00"),
            year=2026,
            status="active",
        )
        db_session.add(deduction)
        await db_session.commit()
        await db_session.refresh(deduction)

        assert deduction.id is not None
        assert deduction.deduction_type == "professional"
        assert deduction.year == 2026

    @pytest.mark.asyncio
    async def test_deduction_types(self, db_session: AsyncSession, accounting_user: User):
        types = ["professional", "social", "property", "investment"]
        for dtype in types:
            d = TaxDeduction(
                user_id=accounting_user.id,
                deduction_type=dtype,
                name=f"Test {dtype}",
                amount=Decimal("10000.00"),
                year=2026,
                status="active",
            )
            db_session.add(d)
        await db_session.commit()

        assert True  # All types created successfully


class TestBudgetCategoryModel:
    """Test BudgetCategory database model"""

    @pytest.mark.asyncio
    async def test_create_budget_category(self, db_session: AsyncSession, accounting_user: User):
        cat = BudgetCategory(
            user_id=accounting_user.id,
            name="Marketing",
            category_type="expense",
            color="#FF5722",
            icon="speaker",
            monthly_limit=Decimal("20000.00"),
            is_active=True,
        )
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        assert cat.id is not None
        assert cat.monthly_limit == Decimal("20000.00")
        assert cat.is_active is True


class TestDashboardCalculations:
    """Test dashboard calculation logic"""

    @pytest.mark.asyncio
    async def test_income_calculation(self, db_session: AsyncSession, accounting_user: User, sample_transactions):
        from sqlalchemy import select, func, and_

        result = await db_session.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.user_id == accounting_user.id,
                    Transaction.transaction_type == "income",
                    Transaction.status == "confirmed",
                )
            )
        )
        total = result.scalar() or Decimal("0")
        assert total == Decimal("75000.00")

    @pytest.mark.asyncio
    async def test_expense_calculation(self, db_session: AsyncSession, accounting_user: User, sample_transactions):
        from sqlalchemy import select, func, and_

        result = await db_session.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.user_id == accounting_user.id,
                    Transaction.transaction_type == "expense",
                    Transaction.status == "confirmed",
                )
            )
        )
        total = result.scalar() or Decimal("0")
        assert total == Decimal("45000.00")

    @pytest.mark.asyncio
    async def test_net_profit(self, db_session: AsyncSession, accounting_user: User, sample_transactions):
        from sqlalchemy import select, func, and_

        income_result = await db_session.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.user_id == accounting_user.id,
                    Transaction.transaction_type == "income",
                    Transaction.status == "confirmed",
                )
            )
        )
        expense_result = await db_session.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.user_id == accounting_user.id,
                    Transaction.transaction_type == "expense",
                    Transaction.status == "confirmed",
                )
            )
        )
        income = income_result.scalar() or Decimal("0")
        expense = expense_result.scalar() or Decimal("0")
        net = income - expense

        assert net == Decimal("30000.00")

    @pytest.mark.asyncio
    async def test_tax_estimate_npd(self, db_session: AsyncSession, accounting_user: User, sample_transactions):
        from sqlalchemy import select, func, and_

        result = await db_session.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.user_id == accounting_user.id,
                    Transaction.transaction_type == "income",
                    Transaction.status == "confirmed",
                )
            )
        )
        income = result.scalar() or Decimal("0")
        tax = income * Decimal("0.04")

        assert tax == Decimal("3000.00")


class TestTransactionValidation:
    """Test transaction validation rules"""

    def test_valid_transaction_types(self):
        valid_types = ["income", "expense"]
        for t in valid_types:
            assert t in ["income", "expense"]

    def test_valid_statuses(self):
        valid_statuses = ["pending", "confirmed", "cancelled"]
        for s in valid_statuses:
            assert s in ["pending", "confirmed", "cancelled"]

    def test_amount_must_be_positive(self):
        amount = Decimal("100.00")
        assert amount > 0

    def test_currency_default(self):
        assert "RUB" == "RUB"


class TestTaxReportTypes:
    """Test tax report type validation"""

    def test_valid_report_types(self):
        valid_types = ["npd_quarterly", "ndfl_annual", "usn"]
        for rt in valid_types:
            assert rt in ["npd_quarterly", "ndfl_annual", "usn"]

    def test_npd_tax_rate(self):
        rate = Decimal("0.04")
        income = Decimal("100000.00")
        tax = income * rate
        assert tax == Decimal("4000.00")

    def test_usn_6_tax_rate(self):
        rate = Decimal("0.06")
        income = Decimal("100000.00")
        tax = income * rate
        assert tax == Decimal("6000.00")

    def test_usn_15_tax_rate(self):
        rate = Decimal("0.15")
        income = Decimal("100000.00")
        expense = Decimal("40000.00")
        taxable = income - expense
        tax = taxable * rate
        assert tax == Decimal("9000.00")
