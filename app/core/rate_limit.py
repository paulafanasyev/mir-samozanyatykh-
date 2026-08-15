"""
Rate limiting configuration - Security Hardened v8.4.1
ANO TsPS INN 9724016805
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    # Authentication endpoints
    "auth_login": "5/minute",
    "auth_2fa": "3/minute",
    "auth_register": "3/hour",
    "auth_password_reset": "3/hour",
    "auth_password_reset_confirm": "5/minute",
    "auth_refresh": "10/minute",

    # AI endpoints
    "svetlana_chat": "30/minute",
    "svetlana_voice": "10/minute",

    # Webhook endpoints
    "webhook_test": "5/minute",
    "webhook_create": "10/hour",

    # Import/Export
    "import_data": "5/hour",
    "export_data": "10/hour",

    # General API
    "api_general": "100/minute",
    "health_check": "60/minute",
}


def get_rate_limit(endpoint: str) -> str:
    """Get rate limit for specific endpoint"""
    return RATE_LIMITS.get(endpoint, "100/minute")
