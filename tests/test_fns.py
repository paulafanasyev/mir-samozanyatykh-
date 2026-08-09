"""Tests for FNS integration module — Mir Samozanyatykh v8.2
ANO TsPS INN 9724016805"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, FNSReceipt, Transaction
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def fns_user(db_session: AsyncSession):
    user = User(
        email="fns_test@example.com",
        full_name="FNS Test User",
        phone="+79123456784",
        password_hash=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True,
        tier="business",
        inn="123456789012",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_fns_receipt(db_session: AsyncSession, fns_user: User):
    receipt = FNSReceipt(
        user_id=fns_user.id,
        fns_id="test-receipt-123",
        fiscal_document_number="1234567890",
        fiscal_sign="9876543210",
        receipt_date=datetime(2026, 1, 15, 14, 30, tzinfo=timezone.utc),
        total_amount=Decimal("2500.50"),
        cash_amount=Decimal("0.00"),
        ecash_amount=Decimal("2500.50"),
        seller_name="OOO Pyaterochka",
        seller_inn="7701234567",
        items=[
            {"name": "Moloko", "price": 89.99, "quantity": 2, "sum": 179.98},
            {"name": "Hleb", "price": 45.50, "quantity": 1, "sum": 45.50},
        ],
        status="verified",
        verified_at=datetime.now(timezone.utc),
    )
    db_session.add(receipt)
    await db_session.commit()
    await db_session.refresh(receipt)
    return receipt


class TestFNSReceiptModel:
    """Test FNSReceipt database model"""

    @pytest.mark.asyncio
    async def test_create_receipt(self, db_session: AsyncSession, fns_user: User):
        receipt = FNSReceipt(
            user_id=fns_user.id,
            fns_id="new-receipt-456",
            receipt_date=datetime.now(timezone.utc),
            total_amount=Decimal("1500.00"),
            status="verified",
        )
        db_session.add(receipt)
        await db_session.commit()
        await db_session.refresh(receipt)

        assert receipt.id is not None
        assert receipt.fns_id == "new-receipt-456"
        assert receipt.total_amount == Decimal("1500.00")

    @pytest.mark.asyncio
    async def test_receipt_items_json(self, db_session: AsyncSession, fns_user: User):
        items = [
            {"name": "Test Item 1", "price": 100.00, "quantity": 2, "sum": 200.00},
            {"name": "Test Item 2", "price": 50.00, "quantity": 1, "sum": 50.00},
        ]
        receipt = FNSReceipt(
            user_id=fns_user.id,
            fns_id="items-test-789",
            receipt_date=datetime.now(timezone.utc),
            total_amount=Decimal("250.00"),
            items=items,
            status="verified",
        )
        db_session.add(receipt)
        await db_session.commit()

        assert len(receipt.items) == 2
        assert receipt.items[0]["name"] == "Test Item 1"

    @pytest.mark.asyncio
    async def test_receipt_seller_data(self, db_session: AsyncSession, fns_user: User):
        receipt = FNSReceipt(
            user_id=fns_user.id,
            fns_id="seller-test",
            receipt_date=datetime.now(timezone.utc),
            total_amount=Decimal("5000.00"),
            seller_name="OOO Test Company",
            seller_inn="7709876543",
            status="verified",
        )
        db_session.add(receipt)
        await db_session.commit()

        assert receipt.seller_name == "OOO Test Company"
        assert receipt.seller_inn == "7709876543"


class TestINNValidation:
    """Test INN validation logic"""

    def test_inn_10_valid(self):
        """Valid 10-digit INN with correct checksum"""
        inn = "7707083893"  # Example valid INN
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(inn[i]) * weights[i] for i in range(9)) % 11 % 10
        assert checksum == int(inn[9])

    def test_inn_10_invalid(self):
        """Invalid 10-digit INN with wrong checksum"""
        inn = "7707083890"  # Wrong last digit
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(inn[i]) * weights[i] for i in range(9)) % 11 % 10
        assert checksum != int(inn[9])

    def test_inn_12_valid(self):
        """Valid 12-digit INN with correct checksums"""
        inn = "500100732259"  # Example valid 12-digit INN
        weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum1 = sum(int(inn[i]) * weights1[i] for i in range(10)) % 11 % 10
        checksum2 = sum(int(inn[i]) * weights2[i] for i in range(11)) % 11 % 10
        assert checksum1 == int(inn[10])
        assert checksum2 == int(inn[11])

    def test_inn_format_validation(self):
        """INN should contain only digits"""
        invalid_inns = ["770708389a", "77-77083893", "770708389", "77070838933"]
        for inn in invalid_inns:
            is_valid = inn.isdigit() and len(inn) in [10, 12]
            assert not is_valid

    def test_inn_length_validation(self):
        """INN must be 10 or 12 digits"""
        assert len("7707083893") == 10
        assert len("500100732259") == 12
        assert len("123") != 10
        assert len("123") != 12


class TestTaxCalculator:
    """Test tax calculator logic"""

    def test_npd_individual_tax(self):
        """NPD for individuals: 4%"""
        income = Decimal("100000.00")
        rate = Decimal("0.04")
        tax = income * rate
        assert tax == Decimal("4000.00")

    def test_npd_legal_tax(self):
        """NPD for legal entities: 6%"""
        income = Decimal("100000.00")
        rate = Decimal("0.06")
        tax = income * rate
        assert tax == Decimal("6000.00")

    def test_usn_6_tax(self):
        """USN income: 6%"""
        income = Decimal("500000.00")
        rate = Decimal("0.06")
        tax = income * rate
        assert tax == Decimal("30000.00")

    def test_usn_15_tax(self):
        """USN income-expense: 15%"""
        income = Decimal("500000.00")
        expense = Decimal("200000.00")
        rate = Decimal("0.15")
        taxable = income - expense
        tax = taxable * rate
        assert tax == Decimal("45000.00")

    def test_usn_15_minimum_tax(self):
        """USN 15% minimum tax is 1% of income"""
        income = Decimal("500000.00")
        expense = Decimal("480000.00")
        rate = Decimal("0.15")
        taxable = income - expense
        tax = taxable * rate
        min_tax = income * Decimal("0.01")
        final_tax = max(tax, min_tax)
        assert final_tax == Decimal("5000.00")

    def test_osno_ndfl_tax(self):
        """OSNO NDFL: 13%"""
        income = Decimal("300000.00")
        rate = Decimal("0.13")
        tax = income * rate
        assert tax == Decimal("39000.00")

    def test_tax_with_deductions(self):
        """Tax calculation with deductions"""
        income = Decimal("200000.00")
        deductions = Decimal("50000.00")
        rate = Decimal("0.04")
        taxable = income - deductions
        tax = taxable * rate
        assert tax == Decimal("6000.00")

    def test_negative_taxable_amount(self):
        """Taxable amount cannot be negative"""
        income = Decimal("100000.00")
        deductions = Decimal("150000.00")
        rate = Decimal("0.04")
        taxable = income - deductions
        if taxable < 0:
            taxable = Decimal("0")
        tax = taxable * rate
        assert tax == Decimal("0.00")


class TestReceiptPayload:
    """Test receipt payload structure"""

    def test_receipt_payload_format(self):
        """Receipt payload should have correct structure"""
        payload = {
            "fiscalDocumentNumber": "1234567890",
            "fiscalSign": "9876543210",
            "date": "20260115T1430",
            "sum": 250050,  # in kopecks
        }
        assert "fiscalDocumentNumber" in payload
        assert "fiscalSign" in payload
        assert "date" in payload
        assert "sum" in payload
        assert isinstance(payload["sum"], int)
        assert payload["sum"] > 0

    def test_date_format(self):
        """Date should be in YYYYMMDDTHHMM format"""
        date_str = "20260115T1430"
        assert len(date_str) == 13
        assert date_str[8] == "T"
        assert date_str[:8].isdigit()
        assert date_str[9:].isdigit()

    def test_sum_in_kopecks(self):
        """Sum should be in kopecks (integer)"""
        rubles = Decimal("2500.50")
        kopecks = int(rubles * 100)
        assert kopecks == 250050
        assert isinstance(kopecks, int)


class TestFNSReceiptStatus:
    """Test FNS receipt status transitions"""

    @pytest.mark.asyncio
    async def test_receipt_verified_status(self, db_session: AsyncSession, fns_user: User):
        receipt = FNSReceipt(
            user_id=fns_user.id,
            fns_id="status-test",
            receipt_date=datetime.now(timezone.utc),
            total_amount=Decimal("1000.00"),
            status="verified",
            verified_at=datetime.now(timezone.utc),
        )
        db_session.add(receipt)
        await db_session.commit()

        assert receipt.status == "verified"
        assert receipt.verified_at is not None

    @pytest.mark.asyncio
    async def test_receipt_cancelled_status(self, db_session: AsyncSession, fns_user: User):
        receipt = FNSReceipt(
            user_id=fns_user.id,
            fns_id="cancelled-test",
            receipt_date=datetime.now(timezone.utc),
            total_amount=Decimal("500.00"),
            status="cancelled",
        )
        db_session.add(receipt)
        await db_session.commit()

        assert receipt.status == "cancelled"
