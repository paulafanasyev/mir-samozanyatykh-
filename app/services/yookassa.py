"""
YooKassa payment service with webhook signature verification
MIR Samozanyatykh v8.4.1 - Security Hardened
ANO TsPS INN 9724016805
"""

import hmac
import hashlib
import json
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.logging import logger


class YooKassaService:
    """YooKassa payment processing with secure webhook verification"""

    def __init__(self):
        self.shop_id = settings.YOOKASSA_SHOP_ID
        self.secret_key = settings.YOOKASSA_SECRET_KEY

    def verify_webhook(self, signature: str, body: bytes) -> bool:
        """
        Verify YooKassa webhook signature using HMAC-SHA256

        Args:
            signature: Signature from X-YooKassa-Signature header
            body: Raw request body bytes

        Returns:
            True if signature is valid
        """
        if not self.secret_key:
            logger.error("YOOKASSA_SECRET_KEY not configured")
            return False

        if not signature:
            logger.warning("Missing webhook signature")
            return False

        # Calculate expected signature
        expected = hmac.new(
            self.secret_key.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected, signature)

    def verify_webhook_ip(self, client_ip: str) -> bool:
        """
        Verify webhook request comes from YooKassa IP range

        YooKassa webhooks come from specific IP ranges.
        This adds an additional layer of security.
        """
        # YooKassa production IPs (update as needed)
        allowed_ips = {
            "185.71.76.0/27",
            "185.71.77.0/27",
            "77.75.153.0/25",
            "77.75.156.11",
            "77.75.156.35",
            "77.75.154.128/25",
            "2a02:5180::/32",
        }

        import ipaddress
        try:
            client = ipaddress.ip_address(client_ip)
            for allowed in allowed_ips:
                if "/" in allowed:
                    if client in ipaddress.ip_network(allowed, strict=False):
                        return True
                else:
                    if client == ipaddress.ip_address(allowed):
                        return True
            return False
        except ValueError:
            return False

    def process_payment_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process validated payment notification"""
        event = data.get("event", "")
        payment = data.get("object", {})

        return {
            "event": event,
            "payment_id": payment.get("id"),
            "status": payment.get("status"),
            "amount": payment.get("amount", {}).get("value"),
            "currency": payment.get("amount", {}).get("currency"),
            "description": payment.get("description"),
            "metadata": payment.get("metadata", {}),
        }


yookassa_service_instance = YooKassaService()
