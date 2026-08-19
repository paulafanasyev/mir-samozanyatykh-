"""Database model tests for Mir Samozanyatykh v6.4"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal


@pytest.mark.asyncio
class TestUserModel:
    async def test_user_creation(self, test_user):
        assert test_user.email == "test@example.com"
        assert test_user.full_name == "Test User"
        assert test_user.is_active
        assert test_user.user_tier == "free"
        assert test_user.role == "user"

    async def test_user_password_verification(self, test_user):
        from app.core.security import verify_password
        assert verify_password("TestPass123!", test_user.password_hash)
        assert not verify_password("wrong", test_user.password_hash)

    async def test_user_role_admin(self, test_user):
        test_user.is_admin = True
        assert test_user.role == "admin"
        test_user.is_moderator = True
        assert test_user.role == "admin"

    async def test_user_tier(self, test_user):
        assert test_user.user_tier == "free"
        test_user.subscription_tier = "pro"
        assert test_user.user_tier == "pro"


@pytest.mark.asyncio
class TestProductModel:
    async def test_product_creation(self, db_session, test_user):
        from app.models import Product
        product = Product(
            user_id=test_user.id,
            name="Konsultatsiya",
            description="IT konsultatsiya",
            price=Decimal("5000.00"),
            unit="chas",
            sku="CONS-001",
        )
        db_session.add(product)
        await db_session.commit()
        assert product.id
        assert product.name == "Konsultatsiya"
        assert product.is_active
        assert product.price == Decimal("5000.00")

    async def test_product_inactive(self, db_session, test_user):
        from app.models import Product
        product = Product(
            user_id=test_user.id,
            name="Arhivnyy produkt",
            price=Decimal("1000.00"),
            is_active=False,
        )
        db_session.add(product)
        await db_session.commit()
        assert not product.is_active


@pytest.mark.asyncio
class TestClientModel:
    async def test_client_creation(self, db_session, test_user):
        from app.models import Client
        client = Client(
            user_id=test_user.id,
            name="OOO Romashka",
            email="romashka@example.com",
            phone="+74444444444",
            company="OOO Romashka",
            inn="7701234567",
        )
        db_session.add(client)
        await db_session.commit()
        assert client.id
        assert client.name == "OOO Romashka"
        assert client.status == "active"
        assert client.inn == "7701234567"

    async def test_client_vip(self, db_session, test_user):
        from app.models import Client
        client = Client(
            user_id=test_user.id,
            name="VIP Klient",
            status="vip",
        )
        db_session.add(client)
        await db_session.commit()
        assert client.status == "vip"


@pytest.mark.asyncio
class TestInvoiceModel:
    async def test_invoice_creation(self, db_session, test_user):
        from app.models import Invoice, InvoiceItem
        invoice = Invoice(
            user_id=test_user.id,
            invoice_number="INV-2024-001",
            total_amount=Decimal("15000.00"),
            status="draft",
        )
        db_session.add(invoice)
        await db_session.commit()
        assert invoice.id
        assert invoice.status == "draft"
        assert invoice.total_amount == Decimal("15000.00")

    async def test_invoice_with_items(self, db_session, test_user):
        from app.models import Invoice, InvoiceItem
        invoice = Invoice(
            user_id=test_user.id,
            invoice_number="INV-2024-002",
            total_amount=Decimal("20000.00"),
            status="sent",
        )
        db_session.add(invoice)
        await db_session.commit()

        item = InvoiceItem(
            invoice_id=invoice.id,
            description="Razrabotka saita",
            quantity=Decimal("10.00"),
            unit_price=Decimal("2000.00"),
            total_price=Decimal("20000.00"),
        )
        db_session.add(item)
        await db_session.commit()
        assert item.id
        assert item.invoice_id == invoice.id


@pytest.mark.asyncio
class TestDealModel:
    async def test_deal_creation(self, db_session, test_user):
        from app.models import Deal
        deal = Deal(
            user_id=test_user.id,
            title="Novyy proekt",
            amount=Decimal("100000.00"),
            status="new",
            priority="high",
        )
        db_session.add(deal)
        await db_session.commit()
        assert deal.id
        assert deal.status == "new"
        assert deal.priority == "high"
        assert deal.amount == Decimal("100000.00")


@pytest.mark.asyncio
class TestContractTemplateModel:
    async def test_template_creation(self, db_session):
        from app.models import ContractTemplate
        template = ContractTemplate(
            name="Dogovor GPH",
            category="gpd",
            content="Shablon dogovora GPH...",
            variables=["client_name", "amount", "date"],
            is_premium=False,
            is_active=True,
        )
        db_session.add(template)
        await db_session.commit()
        assert template.id
        assert template.category == "gpd"
        assert template.is_active


@pytest.mark.asyncio
class TestUserSessionModel:
    async def test_session_creation(self, db_session, test_user):
        from app.models import UserSession
        from datetime import timedelta
        session = UserSession(
            user_id=test_user.id,
            jti="test-jti-12345",
            token_type="access",
            ip_address="127.0.0.1",
            user_agent="pytest",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(session)
        await db_session.commit()
        assert session.id
        assert session.jti == "test-jti-12345"
        assert not session.revoked


@pytest.mark.asyncio
class TestAuditLogModel:
    async def test_audit_log_creation(self, db_session, test_user):
        from app.models import AuditLog
        log = AuditLog(
            user_id=test_user.id,
            action="login",
            resource="auth",
            details="Successful login",
            ip_address="127.0.0.1",
            success=True,
        )
        db_session.add(log)
        await db_session.commit()
        assert log.id
        assert log.action == "login"
        assert log.success
