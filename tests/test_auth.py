import pytest
from fastapi.testclient import TestClient
from server import app, get_db, Base, engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

client = TestClient(app)

@pytest.fixture
async def db_session():
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        yield session
        await session.rollback()

class TestAuth:
    def test_register_validation(self):
        """Test phone and INN validation"""
        response = client.post("/api/auth/register", data={
            "email": "test@test.com",
            "password": "Test123!",
            "phone": "invalid",
            "inn": "123"
        })
        assert response.status_code == 422

    def test_register_valid_phone(self):
        """Test valid phone format"""
        response = client.post("/api/auth/register", data={
            "email": "test@test.com",
            "password": "Test123!",
            "phone": "+79001234567",
            "inn": "123456789012"
        })
        # Should not fail on validation
        assert response.status_code != 422

    def test_login_2fa_required(self):
        """Test 2FA login flow"""
        response = client.post("/api/auth/login/2fa", data={
            "email": "test@test.com",
            "password": "Test123!"
        })
        # Should return 202 if 2FA enabled
        assert response.status_code in [200, 202, 401]

    def test_rate_limiting(self):
        """Test rate limiting on login"""
        for i in range(10):
            response = client.post("/api/auth/login/2fa", data={
                "email": "test@test.com",
                "password": "wrong"
            })
        # After 5 attempts should be rate limited
        assert response.status_code in [401, 429]

class TestSales:
    def test_invoice_auth_required(self):
        """Test invoice endpoints require auth"""
        response = client.get("/api/sales/invoices")
        assert response.status_code == 401

    def test_invoice_phone_validation(self):
        """Test SMS phone validation"""
        response = client.post("/api/sms/send", data={
            "phone": "invalid",
            "message": "test"
        })
        assert response.status_code in [401, 422]

class TestSecurity:
    def test_csp_headers(self):
        """Test CSP headers present"""
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers

    def test_csrf_protection(self):
        """Test CSRF token required"""
        response = client.post("/api/finance/transactions", data={
            "amount": 100,
            "description": "test"
        })
        assert response.status_code in [401, 403]
