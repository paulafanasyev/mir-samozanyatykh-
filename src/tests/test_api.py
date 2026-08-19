"""API tests for Mir Samozanyatykh v6.4"""
import pytest
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
class TestAuthAPI:
    async def test_register_user(self, db_session):
        from app.core.security import get_password_hash
        from app.models import User

        user = User(
            email="newuser@example.com",
            full_name="New User",
            password_hash=get_password_hash("NewPass123!"),
            is_active=True,
            is_verified=False,
        )
        db_session.add(user)
        await db_session.commit()

        assert user.id
        assert user.email == "newuser@example.com"
        assert not user.is_verified

    async def test_user_login_attempts(self, db_session, test_user):
        test_user.failed_login_attempts = 3
        await db_session.commit()
        assert test_user.failed_login_attempts == 3

        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        await db_session.commit()
        assert test_user.locked_until is not None

    async def test_user_lockout_reset(self, db_session, test_user):
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        await db_session.commit()

        test_user.failed_login_attempts = 0
        test_user.locked_until = None
        await db_session.commit()
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None


@pytest.mark.asyncio
class TestSalesAPI:
    async def test_product_list(self, db_session, test_user):
        from app.models import Product

        for i in range(3):
            product = Product(
                user_id=test_user.id,
                name=f"Produkt {i}",
                price=1000 * (i + 1),
            )
            db_session.add(product)
        await db_session.commit()

        result = await db_session.execute(
            Product.__table__.select().where(Product.user_id == test_user.id)
        )
        products = result.scalars().all()
        assert len(products) == 3

    async def test_invoice_status_flow(self, db_session, test_user):
        from app.models import Invoice

        invoice = Invoice(
            user_id=test_user.id,
            invoice_number="INV-TEST-001",
            total_amount=5000,
            status="draft",
        )
        db_session.add(invoice)
        await db_session.commit()

        invoice.status = "sent"
        await db_session.commit()
        assert invoice.status == "sent"

        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
        await db_session.commit()
        assert invoice.status == "paid"
        assert invoice.paid_at is not None


@pytest.mark.asyncio
class TestCRMAPI:
    async def test_client_search(self, db_session, test_user):
        from app.models import Client

        client = Client(
            user_id=test_user.id,
            name="OOO Romashka",
            email="romashka@test.com",
            status="active",
        )
        db_session.add(client)
        await db_session.commit()

        from sqlalchemy import select
        result = await db_session.execute(
            select(Client).where(
                Client.user_id == test_user.id,
                Client.name.ilike("%romashka%")
            )
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.name == "OOO Romashka"

    async def test_deal_pipeline(self, db_session, test_user):
        from app.models import Deal

        deal = Deal(
            user_id=test_user.id,
            title="Bolshoy proekt",
            amount=100000,
            status="new",
            priority="high",
        )
        db_session.add(deal)
        await db_session.commit()

        deal.status = "negotiation"
        await db_session.commit()
        assert deal.status == "negotiation"

        deal.status = "won"
        await db_session.commit()
        assert deal.status == "won"


@pytest.mark.asyncio
class TestContractsAPI:
    async def test_contract_template_list(self, db_session):
        from app.models import ContractTemplate

        templates = [
            ContractTemplate(name="GPH", category="gpd", content="GPH content..."),
            ContractTemplate(name="IT Outsourcing", category="it_outsource", content="IT content..."),
            ContractTemplate(name="NDA", category="nda", content="NDA content...", is_premium=True),
        ]
        for t in templates:
            db_session.add(t)
        await db_session.commit()

        result = await db_session.execute(
            ContractTemplate.__table__.select().where(ContractTemplate.is_active == True)
        )
        active = result.scalars().all()
        assert len(active) == 3

    async def test_signed_contract_creation(self, db_session, test_user):
        from app.models import SignedContract

        contract = SignedContract(
            user_id=test_user.id,
            template_type="gpd",
            title="Dogovor GPH s klientom",
            contract_data={"client": "OOO Test", "amount": "50000"},
            status="draft",
        )
        db_session.add(contract)
        await db_session.commit()

        assert contract.id
        assert contract.status == "draft"
        assert contract.contract_data["client"] == "OOO Test"
