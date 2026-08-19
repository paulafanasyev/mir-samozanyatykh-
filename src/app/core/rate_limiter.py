"""Distributed rate limiting backed by Redis with a development-only local fallback."""

import time
from typing import Dict
from functools import wraps

from fastapi import Request, HTTPException
from app.core.config import settings

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover
    Redis = None


class RateLimiter:
    TIER_LIMITS = {
        "free": {"api": (100, 3600), "svetlana": (20, 86400), "emails": (10, 86400), "webhooks": (5, 86400), "exports": (3, 86400)},
        "pro": {"api": (1000, 3600), "svetlana": (200, 86400), "emails": (100, 86400), "webhooks": (50, 86400), "exports": (20, 86400)},
        "business": {"api": (5000, 3600), "svetlana": (-1, 86400), "emails": (1000, 86400), "webhooks": (200, 86400), "exports": (100, 86400)},
        "enterprise": {"api": (-1, 3600), "svetlana": (-1, 86400), "emails": (-1, 86400), "webhooks": (-1, 86400), "exports": (-1, 86400)},
    }

    def __init__(self):
        self._storage: Dict[str, Dict] = {}
        self._redis = None
        self._redis_error_logged = False

    async def _get_redis(self):
        if Redis is None:
            return None
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_DB_RATE_LIMIT,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        try:
            await self._redis.ping()
            return self._redis
        except Exception:
            return None

    def _get_key(self, user_id: int, endpoint_type: str, window_start: int) -> str:
        return f"rl:{user_id}:{endpoint_type}:{window_start}"

    async def is_allowed(self, user_id: int, tier: str, endpoint_type: str) -> tuple:
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])
        limit, window = limits.get(endpoint_type, (100, 3600))
        if limit == -1:
            return True, -1, 0

        now = int(time.time())
        window_start = now - (now % window)
        reset_time = window_start + window
        redis = await self._get_redis()

        if redis is not None:
            key = self._get_key(user_id, endpoint_type, window_start)
            try:
                count = await redis.incr(key)
                if count == 1:
                    await redis.expire(key, window + 2)
                if count > limit:
                    return False, 0, reset_time
                return True, limit - count, reset_time
            except Exception:
                redis = None

        # Local fallback is deliberately allowed only outside production.
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(status_code=503, detail="Rate limiting service unavailable")

        key = self._get_key(user_id, endpoint_type, window_start)
        entry = self._storage.setdefault(key, {"count": 0, "window": window_start})
        entry["count"] += 1
        if entry["count"] > limit:
            return False, 0, reset_time
        return True, limit - entry["count"], reset_time

    async def get_status(self, user_id: int, tier: str, endpoint_type: str) -> dict:
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["free"])
        limit, window = limits.get(endpoint_type, (100, 3600))
        if limit == -1:
            return {"limit": "unlimited", "used": 0, "remaining": -1, "reset_at": None}
        now = int(time.time())
        window_start = now - (now % window)
        reset_time = window_start + window
        redis = await self._get_redis()
        if redis is not None:
            try:
                key = self._get_key(user_id, endpoint_type, window_start)
                used = int(await redis.get(key) or 0)
                return {"limit": limit, "used": used, "remaining": max(0, limit - used), "reset_at": reset_time}
            except Exception:
                redis = None
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(status_code=503, detail="Rate limiting service unavailable")
        entry = self._storage.get(self._get_key(user_id, endpoint_type, window_start))
        used = int(entry["count"]) if entry else 0
        return {"limit": limit, "used": used, "remaining": max(0, limit - used), "reset_at": reset_time}


rate_limiter = RateLimiter()


def rate_limit(endpoint_type: str = "api"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            current_user = kwargs.get("current_user")
            if current_user:
                allowed, remaining, reset_time = await rate_limiter.is_allowed(current_user.id, current_user.user_tier, endpoint_type)
                if not allowed:
                    limit = rate_limiter.TIER_LIMITS.get(current_user.user_tier, {}).get(endpoint_type, (100, 3600))[0]
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded for {endpoint_type}. Retry after {max(0, reset_time - int(time.time()))}s",
                        headers={"X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset_time)},
                    )
                if request:
                    request.state.rate_limit_remaining = remaining
                    request.state.rate_limit_reset = reset_time
            return await func(*args, **kwargs)
        return wrapper
    return decorator
