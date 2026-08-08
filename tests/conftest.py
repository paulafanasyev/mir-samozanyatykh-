"""
pytest fixtures для тестирования
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import delete

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models import User, Product, Invoice, InvoiceItem, Client, SignedContract


# Тестовая БД
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_mir_samozanyatykh"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Создание event loop для сессии"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Создание таблиц перед сессией тестов"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    """Создание сессии БД для каждого теста"""
    async with TestSession() as session:
        yield session
        # Очистка после теста
        for table in [InvoiceItem, Invoice, Product, SignedContract, Client, User]:
            await session.execute(delete(table))
        await session.commit()


@pytest_asyncio.fixture
async def client(db_session):
    """HTTP клиент для тестов"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Создание тестового пользователя"""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("TestPass123!"),
        full_name="Тестовый Пользователь",
        phone="+79001234567",
        inn="123456789012",
        is_verified=True,
        is_active=True,
        subscription_tier="business",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client, test_user):
    """Получение авторизационных заголовков"""
    response = await client.post("/api/auth/login", data={
        "email": test_user.email,
        "password": "TestPass123!",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_product(db_session, test_user):
    """Создание тестового продукта"""
    product = Product(
        user_id=test_user.id,
        name="Тестовая услуга",
        description="Описание тестовой услуги",
        price=5000.00,
        unit="шт",
        sku="TEST-001",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest_asyncio.fixture
async def test_client(db_session, test_user):
    """Создание тестового клиента"""
    client_obj = Client(
        user_id=test_user.id,
        name="Тестовый Клиент ООО",
        email="client@example.com",
        phone="+79009876543",
        company="Тестовый Клиент ООО",
        inn="987654321098",
        status="active",
    )
    db_session.add(client_obj)
    await db_session.commit()
    await db_session.refresh(client_obj)
    return client_obj


@pytest_asyncio.fixture
async def test_invoice(db_session, test_user, test_client):
    """Создание тестового счёта"""
    invoice = Invoice(
        user_id=test_user.id,
        invoice_number="СЧ-1-20260115-0001",
        client_id=test_client.id,
        total_amount=10000.00,
        status="draft",
        notes="Тестовый счёт",
    )
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)
    
    item = InvoiceItem(
        invoice_id=invoice.id,
        description="Тестовая позиция",
        quantity=2.0,
        unit_price=5000.00,
        total_price=10000.00,
    )
    db_session.add(item)
    await db_session.commit()
    
    return invoice
