"""
Rate limiting configuration - Security Hardened v8.4.3
ANO TsPS INN 9724016805
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "auth_login": "5/minute",
    "auth_2fa": "3/minute",
    "auth_register": "3/hour",
    "auth_password_reset": "3/hour",
    "auth_password_reset_confirm": "5/minute",
    "auth_refresh": "10/minute",
    "svetlana_chat": "30/minute",
    "svetlana_voice": "10/minute",
    "webhook_test": "5/minute",
    "webhook_create": "10/hour",
    "import_data": "5/hour",
    "export_data": "10/hour",
    "api_general": "100/minute",
    "health_check": "60/minute",
}


def get_rate_limit(endpoint: str) -> str:
    """Get rate limit for a named endpoint."""
    return RATE_LIMITS.get(endpoint, "100/minute")


def rate_limit(limit: str):
    """FastAPI decorator used by API modules, backed by SlowAPI."""
    return limiter.limit(limit)
