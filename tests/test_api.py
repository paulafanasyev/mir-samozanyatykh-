"""
Тесты API — МИР Самозанятых v8.7.0
"""
import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_rate_limit():
    client.get("/api/reset-tests")
    yield


@pytest.fixture
def auth_token():
    response = client.post("/api/auth/login", json={
        "email": "demo@example.com",
        "password": "Demo123!"
    })
    return response.json()["access_token"]

class TestContracts:
    def test_list_contracts(self, auth_token):
        response = client.get("/api/contracts", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_create_contract(self, auth_token):
        response = client.post("/api/contracts", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "title": "Тестовый договор",
            "type": "gpd",
            "client_name": "Тест Клиент",
            "client_inn": "7701234567",
            "amount": 10000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "contract" in data

class TestFinance:
    def test_list_finance(self, auth_token):
        response = client.get("/api/finance", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "balance" in data

    def test_create_finance(self, auth_token):
        response = client.post("/api/finance", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "type": "income",
            "amount": 5000,
            "category": "Тест",
            "description": "Тестовая транзакция"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestCalculator:
    def test_npd_calculation_low(self):
        response = client.post("/api/calculator/npd", json={"amount": 100000, "region": "default"})
        assert response.status_code == 200
        data = response.json()
        assert data["rate"] == 0.04
        assert data["tax"] == 4000

    def test_npd_calculation_mid(self):
        response = client.post("/api/calculator/npd", json={"amount": 3000000, "region": "default"})
        assert response.status_code == 200
        data = response.json()
        assert data["rate"] == 0.06

    def test_npd_calculation_high(self):
        response = client.post("/api/calculator/npd", json={"amount": 10000000, "region": "default"})
        assert response.status_code == 200
        data = response.json()
        assert data["rate"] == 0.08

class TestAdmin:
    def test_admin_stats_as_user(self, auth_token):
        response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 403

    def test_admin_stats_as_admin(self):
        login = client.post("/api/auth/login", json={
            "email": "admin@mirsamozanyatykh.ru",
            "password": "MirSamo2026!Admin#Secure"
        }).json()
        token = login["access_token"]
        response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "users" in data

class TestSvetlana:
    def test_svetlana_chat(self, auth_token):
        response = client.post("/api/svetlana/chat", headers={"Authorization": f"Bearer {auth_token}"}, json={
            "message": "Что такое НПД?"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "НПД" in data["response"]

class TestCBR:
    def test_cbr_rates(self):
        response = client.get("/api/cbr/rates")
        assert response.status_code == 200
        data = response.json()
        assert "USD" in data
        assert "EUR" in data
