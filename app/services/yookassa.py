"""
Интеграция с ЮKassa (YooKassa) для онлайн-оплаты
Документация: https://yookassa.ru/developers/
"""

import base64
import json
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import httpx

from app.core.config import settings
from app.core.logging import logger


class YookassaError(Exception):
    """Ошибка интеграции с ЮKassa"""
    pass


class YookassaService:
    """Сервис для работы с API ЮKassa"""
    
    BASE_URL = "https://api.yookassa.ru/v3"
    
    def __init__(self):
        self.shop_id = settings.YOOKASSA_SHOP_ID
        self.secret_key = settings.YOOKASSA_SECRET_KEY
        if not self.shop_id or not self.secret_key:
            logger.warning("Yookassa credentials not configured")
        
        # Basic auth: shop_id:secret_key в base64
        credentials = base64.b64encode(
            f"{self.shop_id}:{self.secret_key}".encode()
        ).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Idempotence-Key": "",  # будет установлен для каждого запроса
        }
    
    def _get_headers(self, idempotence_key: Optional[str] = None) -> Dict[str, str]:
        """Генерация заголовков с Idempotence-Key"""
        headers = self.headers.copy()
        headers["Idempotence-Key"] = idempotence_key or str(uuid.uuid4())
        return headers
    
    async def create_payment(
        self,
        amount: Decimal,
        description: str,
        invoice_id: int,
        return_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Создание платежа в ЮKassa
        
        Args:
            amount: Сумма платежа
            description: Описание
            invoice_id: ID счёта в нашей системе
            return_url: URL для возврата после оплаты
            metadata: Дополнительные данные
        
        Returns:
            dict: Данные созданного платежа
        """
        if not self.shop_id or not self.secret_key:
            raise YookassaError("Yookassa not configured")
        
        domain = settings.DOMAIN
        return_url = return_url or f"https://{domain}/payment/success"
        
        payload = {
            "amount": {
                "value": str(amount.quantize(Decimal("0.01"))),
                "currency": "RUB",
            },
            "capture": True,  # Автоматическое подтверждение
            "confirmation": {
                "type": "redirect",
                "return_url": return_url,
            },
            "description": description[:128],  # макс 128 символов
            "metadata": {
                "invoice_id": str(invoice_id),
                **(metadata or {}),
            },
            "receipt": {
                "customer": {
                    "email": metadata.get("client_email", "") if metadata else "",
                },
                "items": [
                    {
                        "description": description[:128],
                        "quantity": "1.00",
                        "amount": {
                            "value": str(amount.quantize(Decimal("0.01"))),
                            "currency": "RUB",
                        },
                        "vat_code": "1",  # Без НДС (для самозанятых)
                        "payment_subject": "service",
                        "payment_mode": "full_payment",
                    }
                ],
            },
        }
        
        # Удаляем пустые значения
        if not payload["receipt"]["customer"]["email"]:
            del payload["receipt"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/payments",
                headers=self._get_headers(),
                json=payload,
            )
            
            data = response.json()
            
            if response.status_code != 200:
                logger.error(f"Yookassa create payment error: {data}")
                raise YookassaError(
                    f"Payment creation failed: {data.get('description', 'Unknown error')}"
                )
            
            logger.info(
                f"Yookassa payment created: {data.get('id')} for invoice {invoice_id}"
            )
            return data
    
    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Получение информации о платеже"""
        if not self.shop_id or not self.secret_key:
            raise YookassaError("Yookassa not configured")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/payments/{payment_id}",
                headers=self._get_headers(),
            )
            
            data = response.json()
            
            if response.status_code != 200:
                logger.error(f"Yookassa get payment error: {data}")
                raise YookassaError(f"Failed to get payment: {data.get('description', 'Unknown')}")
            
            return data
    
    async def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """Отмена платежа"""
        if not self.shop_id or not self.secret_key:
            raise YookassaError("Yookassa not configured")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/payments/{payment_id}/cancel",
                headers=self._get_headers(),
                json={},
            )
            
            data = response.json()
            
            if response.status_code != 200:
                logger.error(f"Yookassa cancel error: {data}")
                raise YookassaError(f"Cancel failed: {data.get('description', 'Unknown')}")
            
            logger.info(f"Yookassa payment cancelled: {payment_id}")
            return data
    
    async def create_refund(
        self,
        payment_id: str,
        amount: Decimal,
        description: str = "Возврат платежа",
    ) -> Dict[str, Any]:
        """Создание возврата"""
        if not self.shop_id or not self.secret_key:
            raise YookassaError("Yookassa not configured")
        
        payload = {
            "payment_id": payment_id,
            "amount": {
                "value": str(amount.quantize(Decimal("0.01"))),
                "currency": "RUB",
            },
            "description": description[:128],
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/refunds",
                headers=self._get_headers(),
                json=payload,
            )
            
            data = response.json()
            
            if response.status_code != 200:
                logger.error(f"Yookassa refund error: {data}")
                raise YookassaError(f"Refund failed: {data.get('description', 'Unknown')}")
            
            logger.info(f"Yookassa refund created: {data.get('id')} for payment {payment_id}")
            return data
    
    def verify_webhook(self, body: bytes, signature: str) -> bool:
        """
        Проверка подписи webhook от ЮKassa
        
        ЮKassa отправляет подпись в заголовке X-YooKassa-Signature
        """
        import hmac
        import hashlib
        
        expected = hmac.new(
            self.secret_key.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    @staticmethod
    def extract_invoice_id(metadata: Dict[str, Any]) -> Optional[int]:
        """Извлечение ID счёта из metadata платежа"""
        invoice_id = metadata.get("invoice_id")
        if invoice_id:
            try:
                return int(invoice_id)
            except (ValueError, TypeError):
                pass
        return None


# Singleton instance
yookassa_service = YookassaService()
