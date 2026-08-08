"""Database model tests"""
import pytest
from datetime import datetime, timezone

@pytest.mark.asyncio
class TestUserModel:
    async def test_user_creation(self, test_user):
        assert test_user.email == "test@example.com"
        assert test_user.name == "Test User"
        assert test_user.is_active
        assert test_user.level == 1

    async def test_user_password_verification(self, test_user):
        from server import verify_password
        assert verify_password("TestPass123!", test_user.hashed_password)
        assert not verify_password("wrong", test_user.hashed_password)

    async def test_user_default_values(self, db_session):
        from server import User
        user = User(
            email="defaults@example.com",
            name="Defaults",
            phone="+73333333333",
            hashed_password="hashed",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        assert user.level == 1
        assert user.xp == 0
        assert user.total_income == 0
        assert user.total_tax == 0

@pytest.mark.asyncio
class TestTransactionModel:
    async def test_transaction_creation(self, db_session, test_user):
        from server import Transaction
        tx = Transaction(
            user_id=test_user.id,
            amount=50000.00,
            category="Дизайн",
            description="Логотип для клиента",
            transaction_type="income",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(tx)
        await db_session.commit()
        assert tx.id
        assert tx.amount == 50000.00

@pytest.mark.asyncio
class TestClientModel:
    async def test_client_creation(self, db_session, test_user):
        from server import Client
        client = Client(
            user_id=test_user.id,
            name="ООО Ромашка",
            email="romashka@example.com",
            phone="+74444444444",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(client)
        await db_session.commit()
        assert client.id
        assert client.name == "ООО Ромашка"

@pytest.mark.asyncio
class TestAchievementModel:
    async def test_achievement_unlock(self, db_session, test_user):
        from server import UserAchievement
        ach = UserAchievement(
            user_id=test_user.id,
            achievement_key="first_income",
            name="Первый доход",
            description="Получен первый доход",
            icon="💰",
            xp_reward=100,
            unlocked_at=datetime.now(timezone.utc)
        )
        db_session.add(ach)
        await db_session.commit()
        assert ach.unlocked_at is not None
        assert ach.xp_reward == 100
