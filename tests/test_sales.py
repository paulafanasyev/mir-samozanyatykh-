"""
Тесты модуля продаж
"""

import pytest
from decimal import Decimal


class TestProducts:
    """Тесты CRUD продуктов"""
    
    async def test_create_product(self, client, auth_headers):
        """Создание продукта"""
        response = await client.post("/api/sales/products", headers=auth_headers, json={
            "name": "Новая услуга",
            "description": "Описание",
            "price": 10000.00,
            "unit": "шт",
            "sku": "SKU-001",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Новая услуга"
        assert Decimal(str(data["price"])) == Decimal("10000.00")
        assert data["is_active"] is True
    
    async def test_create_product_invalid_price(self, client, auth_headers):
        """Создание продукта с неверной ценой"""
        response = await client.post("/api/sales/products", headers=auth_headers, json={
            "name": "Тест",
            "price": -100,
        })
        assert response.status_code == 422
    
    async def test_list_products(self, client, auth_headers, test_product):
        """Список продуктов"""
        response = await client.get("/api/sales/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["id"] == test_product.id for p in data)
    
    async def test_get_product(self, client, auth_headers, test_product):
        """Получение продукта по ID"""
        response = await client.get(f"/api/sales/products/{test_product.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["name"] == test_product.name
    
    async def test_get_product_not_found(self, client, auth_headers):
        """Получение несуществующего продукта"""
        response = await client.get("/api/sales/products/99999", headers=auth_headers)
        assert response.status_code == 404
    
    async def test_update_product(self, client, auth_headers, test_product):
        """Обновление продукта"""
        response = await client.put(
            f"/api/sales/products/{test_product.id}",
            headers=auth_headers,
            json={"name": "Обновлённая услуга", "price": 7500.00},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Обновлённая услуга"
        assert Decimal(str(data["price"])) == Decimal("7500.00")
    
    async def test_delete_product(self, client, auth_headers, test_product):
        """Удаление продукта (soft delete)"""
        response = await client.delete(
            f"/api/sales/products/{test_product.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204
        
        # Проверка что is_active = False
        response = await client.get(f"/api/sales/products/{test_product.id}", headers=auth_headers)
        assert response.json()["is_active"] is False
    
    async def test_unauthorized_access(self, client):
        """Доступ без авторизации"""
        response = await client.get("/api/sales/products")
        assert response.status_code == 401


class TestInvoices:
    """Тесты CRUD счетов"""
    
    async def test_create_invoice(self, client, auth_headers, test_client):
        """Создание счёта"""
        response = await client.post("/api/sales/invoices", headers=auth_headers, json={
            "client_id": test_client.id,
            "due_date": "2026-02-15",
            "notes": "Тестовый счёт",
            "items": [
                {"description": "Услуга 1", "quantity": 2, "unit_price": 5000.00},
                {"description": "Услуга 2", "quantity": 1, "unit_price": 3000.00},
            ],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert Decimal(str(data["total_amount"])) == Decimal("13000.00")
        assert len(data["items"]) == 2
        assert data["invoice_number"].startswith("СЧ-")
    
    async def test_create_invoice_empty_items(self, client, auth_headers, test_client):
        """Создание счёта без позиций"""
        response = await client.post("/api/sales/invoices", headers=auth_headers, json={
            "client_id": test_client.id,
            "items": [],
        })
        assert response.status_code == 422
    
    async def test_create_invoice_invalid_client(self, client, auth_headers):
        """Создание счёта с несуществующим клиентом"""
        response = await client.post("/api/sales/invoices", headers=auth_headers, json={
            "client_id": 99999,
            "items": [{"description": "Тест", "quantity": 1, "unit_price": 1000}],
        })
        assert response.status_code == 404
    
    async def test_list_invoices(self, client, auth_headers, test_invoice):
        """Список счетов"""
        response = await client.get("/api/sales/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        assert "pagination" in data
        assert any(i["id"] == test_invoice.id for i in data["invoices"])
    
    async def test_filter_invoices_by_status(self, client, auth_headers, test_invoice):
        """Фильтрация счетов по статусу"""
        response = await client.get("/api/sales/invoices?status=draft", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(i["status"] == "draft" for i in data["invoices"])
    
    async def test_get_invoice(self, client, auth_headers, test_invoice):
        """Получение счёта с позициями"""
        response = await client.get(f"/api/sales/invoices/{test_invoice.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_invoice.id
        assert "items" in data
        assert "payments" in data
    
    async def test_update_invoice(self, client, auth_headers, test_invoice):
        """Обновление счёта"""
        response = await client.put(
            f"/api/sales/invoices/{test_invoice.id}",
            headers=auth_headers,
            json={"notes": "Обновлённые примечания"},
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "Обновлённые примечания"
    
    async def test_update_paid_invoice_fails(self, client, auth_headers, test_invoice, db_session):
        """Нельзя изменить оплаченный счёт"""
        test_invoice.status = "paid"
        await db_session.commit()
        
        response = await client.put(
            f"/api/sales/invoices/{test_invoice.id}",
            headers=auth_headers,
            json={"notes": "Попытка изменить"},
        )
        assert response.status_code == 400
    
    async def test_delete_draft_invoice(self, client, auth_headers, test_invoice):
        """Удаление черновика счёта"""
        response = await client.delete(
            f"/api/sales/invoices/{test_invoice.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204
    
    async def test_delete_non_draft_invoice_fails(self, client, auth_headers, test_invoice, db_session):
        """Нельзя удалить не-черновик"""
        test_invoice.status = "sent"
        await db_session.commit()
        
        response = await client.delete(
            f"/api/sales/invoices/{test_invoice.id}",
            headers=auth_headers,
        )
        assert response.status_code == 400
    
    async def test_send_invoice(self, client, auth_headers, test_invoice):
        """Отправка счёта клиенту"""
        response = await client.post(
            f"/api/sales/invoices/{test_invoice.id}/send",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["invoice_number"] == test_invoice.invoice_number
        assert data["pdf_generated"] is True
    
    async def test_get_invoice_pdf(self, client, auth_headers, test_invoice):
        """Скачивание PDF счёта"""
        response = await client.get(
            f"/api/sales/invoices/{test_invoice.id}/pdf",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestPayments:
    """Тесты платежей"""
    
    async def test_create_manual_payment(self, client, auth_headers, test_invoice):
        """Ручное создание платежа"""
        response = await client.post(
            f"/api/sales/invoices/{test_invoice.id}/payments",
            headers=auth_headers,
            json={"amount": 5000.00, "payment_method": "cash"},
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(str(data["amount"])) == Decimal("5000.00")
        assert data["status"] == "completed"
    
    async def test_full_payment_marks_paid(self, client, auth_headers, test_invoice):
        """Полная оплата меняет статус счёта"""
        response = await client.post(
            f"/api/sales/invoices/{test_invoice.id}/payments",
            headers=auth_headers,
            json={"amount": float(test_invoice.total_amount), "payment_method": "card"},
        )
        assert response.status_code == 200
        
        # Проверка статуса счёта
        invoice_response = await client.get(
            f"/api/sales/invoices/{test_invoice.id}",
            headers=auth_headers,
        )
        assert invoice_response.json()["status"] == "paid"
    
    async def test_list_payments(self, client, auth_headers, test_invoice):
        """Список платежей по счёту"""
        # Создаём платёж
        await client.post(
            f"/api/sales/invoices/{test_invoice.id}/payments",
            headers=auth_headers,
            json={"amount": 1000.00, "payment_method": "sbp"},
        )
        
        response = await client.get(
            f"/api/sales/invoices/{test_invoice.id}/payments",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestSalesStats:
    """Тесты статистики"""
    
    async def test_sales_stats(self, client, auth_headers, test_invoice):
        """Получение статистики продаж"""
        response = await client.get("/api/sales/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_invoices" in data
        assert "total_revenue" in data
        assert "overdue_invoices" in data
    
    async def test_sales_dashboard(self, client, auth_headers, test_invoice):
        """Получение дашборда"""
        response = await client.get("/api/sales/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "monthly_revenue" in data
        assert "recent_invoices" in data
        assert "top_clients" in data


class TestYookassaIntegration:
    """Тесты интеграции ЮKassa (с моками)"""
    
    async def test_create_yookassa_payment(self, client, auth_headers, test_invoice, monkeypatch):
        """Создание платежа ЮKassa"""
        async def mock_create_payment(*args, **kwargs):
            return {
                "id": "test-payment-id",
                "status": "pending",
                "confirmation": {
                    "confirmation_url": "https://yookassa.ru/test-payment",
                },
                "amount": {"value": "10000.00", "currency": "RUB"},
            }
        
        monkeypatch.setattr(
            "app.services.yookassa.yookassa_service.create_payment",
            mock_create_payment,
        )
        
        response = await client.post(
            f"/api/sales/invoices/{test_invoice.id}/yookassa",
            headers=auth_headers,
            json={"invoice_id": test_invoice.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == "test-payment-id"
        assert "confirmation_url" in data
    
    async def test_yookassa_webhook_payment_succeeded(self, client, test_invoice, db_session, monkeypatch):
        """Обработка webhook об успешной оплате"""
        async def mock_verify(*args, **kwargs):
            return True
        
        monkeypatch.setattr(
            "app.services.yookassa.yookassa_service.verify_webhook",
            mock_verify,
        )
        
        response = await client.post("/api/sales/yookassa/webhook", json={
            "event": "payment.succeeded",
            "object": {
                "id": "test-payment-id",
                "status": "succeeded",
                "amount": {"value": "10000.00", "currency": "RUB"},
                "metadata": {"invoice_id": str(test_invoice.id)},
            },
        })
        assert response.status_code == 200
        
        # Проверка что счёт оплачен
        await db_session.refresh(test_invoice)
        assert test_invoice.status == "paid"
    
    async def test_yookassa_webhook_invalid_event(self, client):
        """Webhook с неверным событием"""
        response = await client.post("/api/sales/yookassa/webhook", json={
            "event": "invalid.event",
            "object": {},
        })
        assert response.status_code == 422
