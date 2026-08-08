"""
Тесты модуля договоров
"""

import pytest
from decimal import Decimal


class TestContractTemplates:
    """Тесты шаблонов договоров"""
    
    async def test_list_templates(self, client, auth_headers):
        """Список шаблонов"""
        response = await client.get("/api/contracts/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 0  # может быть пустым если не заполнены
    
    async def test_get_template_detail_gpd(self, client, auth_headers):
        """Детали шаблона ГПД"""
        response = await client.get("/api/contracts/templates/gpd", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "gpd"
        assert "fields" in data
        assert len(data["fields"]) > 0
        assert data["name"] == "Договор ГПД (гражданско-правовой)"
    
    async def test_get_template_detail_it(self, client, auth_headers):
        """Детали IT-шаблона (premium)"""
        response = await client.get("/api/contracts/templates/it_outsource", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "it_outsource"
        assert "fields" in data
    
    async def test_get_invalid_template(self, client, auth_headers):
        """Несуществующий шаблон"""
        response = await client.get("/api/contracts/templates/invalid", headers=auth_headers)
        assert response.status_code == 404


class TestContractGeneration:
    """Тесты генерации договоров"""
    
    async def test_generate_gpd_contract(self, client, auth_headers):
        """Генерация договора ГПД"""
        response = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "gpd",
            "variables": {
                "contractor_name": "Иванов Иван Иванович",
                "contractor_inn": "123456789012",
                "client_name": "ООО Ромашка",
                "client_inn": "987654321098",
                "subject": "Разработка сайта",
                "price": "50000",
                "deadline": "2026-03-01",
                "payment_terms": "50% предоплата, 50% по факту",
            },
            "sign": False,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["template_type"] == "gpd"
        assert data["status"] == "draft"
        assert data["pdf_path"] is not None
    
    async def test_generate_contract_missing_required(self, client, auth_headers):
        """Генерация с незаполненными обязательными полями"""
        response = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "gpd",
            "variables": {
                "contractor_name": "Иванов",
                # пропущены обязательные поля
            },
        })
        assert response.status_code == 400
        assert "обязательные поля" in response.json()["message"]
    
    async def test_generate_premium_without_subscription(self, client, auth_headers, test_user, db_session):
        """Генерация premium шаблона без подписки"""
        test_user.subscription_tier = "free"
        await db_session.commit()
        
        response = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "it_outsource",
            "variables": {
                "contractor_name": "Иванов",
                "contractor_inn": "123456789012",
                "client_name": "ООО Ромашка",
                "client_inn": "987654321098",
                "services": "IT поддержка",
                "monthly_fee": "50000",
                "contract_term": "12",
            },
        })
        assert response.status_code == 403


class TestContractSigning:
    """Тесты подписания договоров"""
    
    async def test_sign_contract(self, client, auth_headers):
        """Подписание договора"""
        # Сначала создаём договор
        create_resp = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "act",
            "variables": {
                "contractor_name": "Иванов И.И.",
                "contractor_inn": "123456789012",
                "client_name": "ООО Ромашка",
                "works_description": "Разработка сайта",
                "total": "50000",
                "act_date": "2026-01-15",
            },
        })
        contract_id = create_resp.json()["id"]
        
        # Подписываем
        response = await client.post(f"/api/contracts/{contract_id}/sign", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "signed"
        assert data["signature_data"] is not None
        assert data["signed_at"] is not None
    
    async def test_sign_already_signed(self, client, auth_headers):
        """Повторное подписание"""
        create_resp = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "act",
            "variables": {
                "contractor_name": "Иванов",
                "contractor_inn": "123456789012",
                "client_name": "Клиент",
                "works_description": "Работы",
                "total": "1000",
                "act_date": "2026-01-15",
            },
        })
        contract_id = create_resp.json()["id"]
        
        # Первое подписание
        await client.post(f"/api/contracts/{contract_id}/sign", headers=auth_headers)
        
        # Второе подписание
        response = await client.post(f"/api/contracts/{contract_id}/sign", headers=auth_headers)
        assert response.status_code == 400
        assert "уже подписан" in response.json()["message"]
    
    async def test_cancel_contract(self, client, auth_headers):
        """Отмена договора"""
        create_resp = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "act",
            "variables": {
                "contractor_name": "Иванов",
                "contractor_inn": "123456789012",
                "client_name": "Клиент",
                "works_description": "Работы",
                "total": "1000",
                "act_date": "2026-01-15",
            },
        })
        contract_id = create_resp.json()["id"]
        
        response = await client.post(f"/api/contracts/{contract_id}/cancel", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
    async def test_cancel_signed_contract_fails(self, client, auth_headers):
        """Нельзя отменить подписанный договор"""
        create_resp = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "act",
            "variables": {
                "contractor_name": "Иванов",
                "contractor_inn": "123456789012",
                "client_name": "Клиент",
                "works_description": "Работы",
                "total": "1000",
                "act_date": "2026-01-15",
            },
        })
        contract_id = create_resp.json()["id"]
        await client.post(f"/api/contracts/{contract_id}/sign", headers=auth_headers)
        
        response = await client.post(f"/api/contracts/{contract_id}/cancel", headers=auth_headers)
        assert response.status_code == 400


class TestContractList:
    """Тесты списка договоров"""
    
    async def test_list_my_contracts(self, client, auth_headers):
        """Список моих договоров"""
        response = await client.get("/api/contracts/my", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    async def test_list_filtered_by_status(self, client, auth_headers):
        """Фильтрация по статусу"""
        response = await client.get("/api/contracts/my?status=draft", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(c["status"] == "draft" for c in data)
    
    async def test_get_contract_detail(self, client, auth_headers):
        """Получение договора по ID"""
        create_resp = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "act",
            "variables": {
                "contractor_name": "Иванов",
                "contractor_inn": "123456789012",
                "client_name": "Клиент",
                "works_description": "Работы",
                "total": "1000",
                "act_date": "2026-01-15",
            },
        })
        contract_id = create_resp.json()["id"]
        
        response = await client.get(f"/api/contracts/{contract_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == contract_id
    
    async def test_get_contract_pdf(self, client, auth_headers):
        """Скачивание PDF договора"""
        create_resp = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "act",
            "variables": {
                "contractor_name": "Иванов",
                "contractor_inn": "123456789012",
                "client_name": "Клиент",
                "works_description": "Работы",
                "total": "1000",
                "act_date": "2026-01-15",
            },
        })
        contract_id = create_resp.json()["id"]
        
        response = await client.get(f"/api/contracts/{contract_id}/pdf", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestContractVerify:
    """Тесты проверки подписи"""
    
    async def test_verify_signed_contract(self, client, auth_headers):
        """Проверка подписанного договора"""
        create_resp = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "act",
            "variables": {
                "contractor_name": "Иванов",
                "contractor_inn": "123456789012",
                "client_name": "Клиент",
                "works_description": "Работы",
                "total": "1000",
                "act_date": "2026-01-15",
            },
        })
        contract_id = create_resp.json()["id"]
        await client.post(f"/api/contracts/{contract_id}/sign", headers=auth_headers)
        
        response = await client.post(f"/api/contracts/{contract_id}/verify", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["signed"] is True
        assert data["valid"] is True
        assert "signature_info" in data
    
    async def test_verify_unsigned_contract(self, client, auth_headers):
        """Проверка неподписанного договора"""
        create_resp = await client.post("/api/contracts/generate", headers=auth_headers, json={
            "template_id": "act",
            "variables": {
                "contractor_name": "Иванов",
                "contractor_inn": "123456789012",
                "client_name": "Клиент",
                "works_description": "Работы",
                "total": "1000",
                "act_date": "2026-01-15",
            },
        })
        contract_id = create_resp.json()["id"]
        
        response = await client.post(f"/api/contracts/{contract_id}/verify", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["signed"] is False
        assert "не подписан" in data["message"]
