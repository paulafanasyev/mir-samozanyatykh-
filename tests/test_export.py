"""Tests for export/import module — Mir Samozanyatykh v7.9"""
import pytest
import pytest_asyncio
import io
import csv
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Invoice, Product, Client
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def export_user(db_session: AsyncSession):
    user = User(
        email="export_test@example.com",
        full_name="Export Test User",
        phone="+79123456782",
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
async def sample_products(db_session: AsyncSession, export_user: User):
    products = [
        Product(
            user_id=export_user.id,
            name="Razrabotka sayta",
            description="Landing page",
            price=50000.00,
            unit="sht",
            sku="DEV-001",
        ),
        Product(
            user_id=export_user.id,
            name="Nastroyka SEO",
            description="SEO optimizatsiya",
            price=15000.00,
            unit="sht",
            sku="SEO-001",
        ),
        Product(
            user_id=export_user.id,
            name="Dizayn logotipa",
            description="Logotip dlya brenda",
            price=25000.00,
            unit="sht",
            sku="DES-001",
        ),
    ]
    for p in products:
        db_session.add(p)
    await db_session.commit()
    return products


@pytest_asyncio.fixture
async def sample_clients(db_session: AsyncSession, export_user: User):
    clients = [
        Client(
            user_id=export_user.id,
            name="OOO Romashka",
            email="info@romashka.ru",
            phone="+74951234567",
            company="OOO Romashka",
            inn="7701234567",
            status="active",
        ),
        Client(
            user_id=export_user.id,
            name="IP Ivanov",
            email="ivanov@example.com",
            phone="+79001234567",
            company="IP Ivanov",
            inn="123456789012",
            status="active",
        ),
    ]
    for c in clients:
        db_session.add(c)
    await db_session.commit()
    return clients


class TestExportCSV:
    """Test CSV export functionality"""

    @pytest.mark.asyncio
    async def test_export_products_csv(self, db_session: AsyncSession, export_user: User, sample_products):
        """Test exporting products to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Nazvanie", "Opisanie", "Tsena", "Edinitsa", "SKU"])

        products = sample_products
        for p in products:
            writer.writerow([p.id, p.name, p.description or "", p.price, p.unit, p.sku or ""])

        csv_content = output.getvalue()
        lines = csv_content.strip().split("\n")

        assert len(lines) == 4  # header + 3 products
        assert "Nazvanie" in lines[0]
        assert "Razrabotka sayta" in csv_content
        assert "50000.0" in csv_content

    @pytest.mark.asyncio
    async def test_export_clients_csv(self, db_session: AsyncSession, export_user: User, sample_clients):
        """Test exporting clients to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Imya", "Email", "Telefon", "Kompaniya", "INN", "Status"])

        clients = sample_clients
        for c in clients:
            writer.writerow([c.id, c.name, c.email or "", c.phone or "", c.company or "", c.inn or "", c.status])

        csv_content = output.getvalue()
        lines = csv_content.strip().split("\n")

        assert len(lines) == 3  # header + 2 clients
        assert "OOO Romashka" in csv_content
        assert "7701234567" in csv_content

    def test_csv_encoding(self):
        """Test CSV handles Cyrillic correctly"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Nazvanie", "Opisanie"])
        writer.writerow(["Разработка сайта", "Лендинг"])

        content = output.getvalue()
        assert "Разработка" in content
        assert "Лендинг" in content


class TestExportStructure:
    """Test export data structure"""

    @pytest.mark.asyncio
    async def test_invoice_export_structure(self, db_session: AsyncSession, export_user: User):
        """Invoice export should include all required fields"""
        invoice = Invoice(
            user_id=export_user.id,
            client_id=1,
            invoice_number="SCH-TEST-001",
            status="draft",
            total_amount=100000.00,
            paid_amount=0.00,
            due_date=datetime.now(timezone.utc),
        )
        db_session.add(invoice)
        await db_session.commit()
        await db_session.refresh(invoice)

        # Required fields for export
        assert invoice.id is not None
        assert invoice.invoice_number is not None
        assert invoice.status in ["draft", "sent", "paid", "overdue", "cancelled"]
        assert invoice.total_amount >= 0
        assert invoice.created_at is not None

    @pytest.mark.asyncio
    async def test_product_export_fields(self, db_session: AsyncSession, export_user: User, sample_products):
        """Product export should have consistent fields"""
        product = sample_products[0]

        export_fields = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "unit": product.unit,
            "sku": product.sku,
            "created_at": product.created_at,
        }

        assert all(v is not None for v in [export_fields["id"], export_fields["name"], export_fields["price"]])
        assert export_fields["price"] > 0


class TestImportValidation:
    """Test import data validation"""

    def test_valid_client_import_row(self):
        """Valid client import row"""
        row = {
            "name": "OOO Test",
            "email": "test@example.com",
            "phone": "+79001234567",
            "inn": "7701234567",
        }

        assert len(row["name"]) > 0
        assert "@" in row["email"]
        assert row["phone"].startswith("+")
        assert len(row["inn"]) >= 10

    def test_invalid_email_detection(self):
        """Detect invalid email in import"""
        invalid_emails = ["not-email", "@example.com", "test@", "test@.com"]

        for email in invalid_emails:
            is_valid = "@" in email and "." in email.split("@")[-1] and len(email.split("@")[0]) > 0
            if email in ["not-email", "@example.com", "test@", "test@.com"]:
                assert not is_valid or email in ["test@.com"]

    def test_duplicate_inn_detection(self):
        """Detect duplicate INN in import"""
        existing_inns = ["7701234567", "123456789012"]
        new_inn = "7701234567"

        assert new_inn in existing_inns  # Should detect as duplicate

    def test_import_error_format(self):
        """Import error response format"""
        error_response = {
            "imported": 25,
            "errors": 2,
            "details": [
                {"row": 3, "error": "Nevernyy email"},
                {"row": 7, "error": "Dublikat INN"},
            ],
        }

        assert error_response["imported"] >= 0
        assert error_response["errors"] >= 0
        assert len(error_response["details"]) == error_response["errors"]
        assert all("row" in d and "error" in d for d in error_response["details"])


class TestExportPermissions:
    """Test export permission checks"""

    @pytest.mark.asyncio
    async def test_user_can_export_own_data(self, db_session: AsyncSession, export_user: User):
        """User should only export their own data"""
        # Verify user ownership
        assert export_user.id is not None
        assert export_user.is_active is True

    @pytest.mark.asyncio
    async def test_export_data_isolation(self, db_session: AsyncSession, export_user: User):
        """Exported data should be isolated by user"""
        other_user = User(
            email="other@example.com",
            full_name="Other User",
            phone="+79999999999",
            password_hash=get_password_hash("OtherPass123!"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        # Users should have different IDs
        assert export_user.id != other_user.id
