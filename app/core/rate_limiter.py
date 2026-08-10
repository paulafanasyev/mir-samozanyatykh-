"""
Rate Limiter v7.4
Продвинутые лимиты по тарифам с Redis
"""

import time
from typing import Optional, Dict
from functools import wraps

from fastapi import Request, HTTPException
from app.core.config import settings


class RateLimiter:
    """Rate limiter с поддержкой разных лимитов по тарифам"""

    # Лимиты по тарифам: (requests, window_seconds)
    TIER_LIMITS = {
        "free": {
            "api": (100, 3600),      # 100 запросов/час
            "svetlana": (20, 86400), # 20 сообщений/день
            "emails": (10, 86400),   # 10 писем/день
            "webhooks": (5, 86400),  # 5 вебхуков/день
            "exports": (3, 86400),   # 3 экспорта/день
        },
        "pro": {
            "api": (1000, 3600),
            "svetlana": (200, 86400),
            "emails": (100, 86400),
            "webhooks": (50, 86400),
            "exports": (20, 86400),
        },
        "business": {
            "api": (5000, 3600),
            "svetlana": (-1, 86400),  # unlimited
            "emails": (1000, 86400),
            "webhooks": (200, 86400),
            "exports": (100, 86400),
        },
        "enterprise": {
            "api": (-1, 3600),  # unlimited
            "svetlana": (-1, 86400),
            "emails": (-1, 86400),
            "webhooks": (-1, 86400),
            "exports": (-1, 86400),
        },
    }

    def __init__(self):
        # In-memory storage (в проде — Redis)
        self._storage: Dict[str, Dict] = {}

    def _get_key(self, user_id: int, endpoint_type: str) -> str:
        return f"rate_limit:{user_id}:{endpoint_type}"

    def is_allowed(self, user_id: int, tier: str, endpoint_type: str) -> tuple:
        """Проверка лимита. Возвращает (allowed, remaining, reset_time)"""
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])
        limit, window = limits.get(endpoint_type, (100, 3600))

        # Unlimited
        if limit == -1:
            return True, -1, 0

        key = self._get_key(user_id, endpoint_type)
        now = int(time.time())
        window_start = now - (now % window)

        if key not in self._storage:
            self._storage[key] = {"count": 0, "window": window_start}

        # Новое окно
        if self._storage[key]["window"] != window_start:
            self._storage[key] = {"count": 0, "window": window_start}

        current_count = self._storage[key]["count"]

        if current_count >= limit:
            reset_time = window_start + window
            return False, 0, reset_time

        self._storage[key]["count"] += 1
        remaining = limit - self._storage[key]["count"]
        reset_time = window_start + window

        return True, remaining, reset_time

    def get_status(self, user_id: int, tier: str, endpoint_type: str) -> dict:
        """Получить статус лимитов"""
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])
        limit, window = limits.get(endpoint_type, (100, 3600))

        if limit == -1:
            return {"limit": "unlimited", "used": 0, "remaining": -1, "reset_at": None}

        key = self._get_key(user_id, endpoint_type)
        now = int(time.time())
        window_start = now - (now % window)

        if key not in self._storage or self._storage[key]["window"] != window_start:
            return {"limit": limit, "used": 0, "remaining": limit, "reset_at": window_start + window}

        used = self._storage[key]["count"]
        return {
            "limit": limit,
            "used": used,
            "remaining": max(0, limit - used),
            "reset_at": self._storage[key]["window"] + window,
        }


rate_limiter = RateLimiter()


def rate_limit(endpoint_type: str = "api"):
    """Декоратор для rate limiting"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Находим request и current_user в kwargs
            request = kwargs.get("request")
            current_user = kwargs.get("current_user")

            if current_user:
                allowed, remaining, reset_time = rate_limiter.is_allowed(
                    current_user.id,
                    current_user.user_tier,
                    endpoint_type,
                )

                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded for {endpoint_type}. Retry after {reset_time - int(time.time())}s",
                        headers={
                            "X-RateLimit-Limit": str(rate_limiter.TIER_LIMITS.get(current_user.user_tier, {}).get(endpoint_type, (100, 3600))[0]),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(reset_time),
                        },
                    )

                # Добавляем заголовки в response
                if request:
                    request.state.rate_limit_remaining = remaining
                    request.state.rate_limit_reset = reset_time

            return await func(*args, **kwargs)
        return wrapper
    return decorator
