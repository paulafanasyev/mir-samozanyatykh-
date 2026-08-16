"""Tests for database models"""
import pytest
from datetime import datetime
from app.models.base import User, Contract, FinanceRecord, Notification, Achievement, UserAchievement, MarketplaceItem, CRMContact, Grant, AuditLog, Payment, SvetlanaChat
from app.core.security import get_password_hash

class TestUserModel:
    def test_create_user(self, db_session):
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            full_name="Тест Пользователь",
            phone="+79123456789",
            inn="123456789012"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role.value == "user"
        assert user.subscription.value == "START"
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_unique_email(self, db_session):
        user1 = User(email="unique@test.com", password_hash="hash1", full_name="User1")
        db_session.add(user1)
        db_session.commit()

        user2 = User(email="unique@test.com", password_hash="hash2", full_name="User2")
        db_session.add(user2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_user_default_values(self, db_session):
        user = User(email="defaults@test.com", password_hash="hash", full_name="Defaults")
        db_session.add(user)
        db_session.commit()

        assert user.login_attempts == 0
        assert user.is_verified is False
        assert user.email_verified is False
        assert user.two_factor_enabled is False

class TestContractModel:
    def test_create_contract(self, db_session, test_user_data):
        user = User(email="contract@test.com", password_hash="hash", full_name="Contract User")
        db_session.add(user)
        db_session.commit()

        contract = Contract(
            user_id=user.id,
            title="Тестовый договор",
            client_name="ООО Тест",
            amount=50000.0,
            description="Описание работ",
            contract_type="gpd"
        )
        db_session.add(contract)
        db_session.commit()

        assert contract.id is not None
        assert contract.status.value == "draft"
        assert contract.user_id == user.id

    def test_contract_amount_positive(self, db_session):
        user = User(email="amount@test.com", password_hash="hash", full_name="Amount")
        db_session.add(user)
        db_session.commit()

        contract = Contract(
            user_id=user.id,
            title="Договор",
            client_name="Клиент",
            amount=0.01,
            contract_type="gpd"
        )
        db_session.add(contract)
        db_session.commit()
        assert contract.amount > 0

class TestFinanceRecord:
    def test_create_finance_record(self, db_session):
        user = User(email="finance@test.com", password_hash="hash", full_name="Finance")
        db_session.add(user)
        db_session.commit()

        record = FinanceRecord(
            user_id=user.id,
            type="income",
            amount=100000.0,
            category="IT-услуги",
            description="Разработка",
            tax_rate=0.04,
            tax_amount=4000.0
        )
        db_session.add(record)
        db_session.commit()

        assert record.id is not None
        assert record.type == "income"
        assert record.tax_amount == 4000.0

class TestNotification:
    def test_create_notification(self, db_session):
        user = User(email="notif@test.com", password_hash="hash", full_name="Notif")
        db_session.add(user)
        db_session.commit()

        notif = Notification(
            user_id=user.id,
            title="Новый договор",
            message="Создан новый договор #123",
            type="info"
        )
        db_session.add(notif)
        db_session.commit()

        assert notif.is_read is False
        assert notif.type.value == "info"

class TestAchievement:
    def test_create_achievement(self, db_session):
        ach = Achievement(
            name="Первый договор",
            description="Создайте первый договор",
            icon="📝",
            points=10,
            condition_type="contracts_count",
            condition_value=1
        )
        db_session.add(ach)
        db_session.commit()

        assert ach.id is not None
        assert ach.points == 10

    def test_user_achievement(self, db_session):
        user = User(email="ach@test.com", password_hash="hash", full_name="Ach")
        db_session.add(user)
        db_session.commit()

        ach = Achievement(name="Тест", description="Тест", points=5)
        db_session.add(ach)
        db_session.commit()

        ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
        db_session.add(ua)
        db_session.commit()

        assert ua.earned_at is not None

class TestMarketplaceItem:
    def test_create_item(self, db_session):
        user = User(email="market@test.com", password_hash="hash", full_name="Market")
        db_session.add(user)
        db_session.commit()

        item = MarketplaceItem(
            seller_id=user.id,
            title="Логотип",
            description="Дизайн логотипа",
            price=15000.0,
            category="Дизайн",
            tags=["логотип", "брендинг"]
        )
        db_session.add(item)
        db_session.commit()

        assert item.views == 0
        assert item.is_active is True

class TestCRMContact:
    def test_create_contact(self, db_session):
        user = User(email="crm@test.com", password_hash="hash", full_name="CRM")
        db_session.add(user)
        db_session.commit()

        contact = CRMContact(
            owner_id=user.id,
            name="Иван Петров",
            email="ivan@example.com",
            phone="+79123456789",
            company="ООО Пример",
            status="lead",
            source="Рекомендация"
        )
        db_session.add(contact)
        db_session.commit()

        assert contact.status == "lead"

class TestGrant:
    def test_create_grant(self, db_session):
        grant = Grant(
            title="Грант на стартап",
            description="Поддержка IT-стартапов",
            organization="Фонд развития",
            amount_min=100000.0,
            amount_max=500000.0,
            category="IT",
            region="Москва"
        )
        db_session.add(grant)
        db_session.commit()

        assert grant.status == "active"
        assert grant.ai_score is None

class TestAuditLog:
    def test_create_audit_log(self, db_session):
        user = User(email="audit@test.com", password_hash="hash", full_name="Audit")
        db_session.add(user)
        db_session.commit()

        log = AuditLog(
            user_id=user.id,
            action="login",
            entity_type="user",
            entity_id=user.id,
            details={"ip": "127.0.0.1"},
            ip_address="127.0.0.1"
        )
        db_session.add(log)
        db_session.commit()

        assert log.created_at is not None

class TestPayment:
    def test_create_payment(self, db_session):
        user = User(email="pay@test.com", password_hash="hash", full_name="Pay")
        db_session.add(user)
        db_session.commit()

        payment = Payment(
            user_id=user.id,
            amount=300.0,
            description="Подписка PRO",
            provider="yookassa",
            subscription_tier="PRO"
        )
        db_session.add(payment)
        db_session.commit()

        assert payment.status.value == "pending"
        assert payment.currency == "RUB"

class TestSvetlanaChat:
    def test_create_chat(self, db_session):
        user = User(email="svet@test.com", password_hash="hash", full_name="Svet")
        db_session.add(user)
        db_session.commit()

        chat = SvetlanaChat(
            user_id=user.id,
            session_id="abc123",
            message="Какой налог для самозанятых?",
            response="4% с физлиц, 6% с юрлиц",
            category="налоги"
        )
        db_session.add(chat)
        db_session.commit()

        assert chat.rating is None
