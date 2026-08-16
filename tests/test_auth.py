"""
Тесты аутентификации — МИР Самозанятых v8.7.0
"""
import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.main import app, hash_password, verify_password, create_jwt, decode_jwt

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_rate_limit():
    client.get("/api/reset-tests")
    yield


class TestAuth:
    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "8.7.0"

    def test_password_hashing(self):
        pwd = "TestPassword123!"
        hashed = hash_password(pwd)
        assert verify_password(hashed, pwd) is True
        assert verify_password(hashed, "wrong") is False

    def test_jwt_create_decode(self):
        token = create_jwt({"sub": "test_user", "role": "user"})
        decoded = decode_jwt(token)
        assert decoded["sub"] == "test_user"
        assert decoded["role"] == "user"

    def test_register_validation(self):
        # Invalid email
        response = client.post("/api/auth/register", json={
            "email": "invalid",
            "password": "short",
            "name": "Test",
            "phone": "+79990000000"
        })
        assert response.status_code == 400

    def test_register_success(self):
        import uuid
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        response = client.post("/api/auth/register", json={
            "email": email,
            "password": "TestPass123!",
            "name": "Тест Пользователь",
            "phone": "+79990000000",
            "inn": "123456789012"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data

    def test_login_success(self):
        # Login as demo user
        response = client.post("/api/auth/login", json={
            "email": "demo@example.com",
            "password": "Demo123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid(self):
        response = client.post("/api/auth/login", json={
            "email": "demo@example.com",
            "password": "wrong_password"
        })
        assert response.status_code == 401

    def test_me_endpoint(self):
        # First login
        login = client.post("/api/auth/login", json={
            "email": "demo@example.com",
            "password": "Demo123!"
        }).json()
        token = login["access_token"]

        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "demo@example.com"

    def test_me_unauthorized(self):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_rate_limiting(self):
        # Multiple failed logins
        for i in range(6):
            response = client.post("/api/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "wrong"
            })
        # After 5 attempts should be rate limited
        assert response.status_code in [401, 429]

    def test_phone_validation(self):
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "name": "Test",
            "phone": "89990000000"  # Invalid format
        })
        assert response.status_code == 400

    def test_inn_validation(self):
        response = client.post("/api/auth/register", json={
            "email": "test2@example.com",
            "password": "TestPass123!",
            "name": "Test",
            "phone": "+79990000000",
            "inn": "123"  # Invalid
        })
        assert response.status_code == 400
