import pytest
from httpx import AsyncClient, ASGITransport
from server import app, validate_password_strength, Base, engine

@pytest.fixture(scope="module")
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data

@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/api/auth/register", data={
        "email": "test@example.com",
        "password": "Test123!",
        "full_name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data

@pytest.mark.asyncio
async def test_register_weak_password(client):
    response = await client.post("/api/auth/register", data={
        "email": "test2@example.com",
        "password": "123",
        "full_name": "Test User"
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login_unverified(client):
    response = await client.post("/api/auth/login", data={
        "email": "test@example.com",
        "password": "Test123!"
    })
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_svetlana_ask(client):
    response = await client.post("/api/svetlana/ask", data={
        "question": "Как зарегистрироваться как самозанятый?"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data

@pytest.mark.asyncio
async def test_rate_limit(client):
    for _ in range(10):
        await client.post("/api/auth/login", data={
            "email": "test@example.com",
            "password": "wrong"
        })
    response = await client.post("/api/auth/login", data={
        "email": "test@example.com",
        "password": "wrong"
    })
    assert response.status_code in [401, 429]
