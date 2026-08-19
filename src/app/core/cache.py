"""Shared cache backed by Redis with a development-only local fallback."""

import json
import hashlib
from typing import Optional, Any
from datetime import datetime, timezone, timedelta

from app.core.config import settings

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover
    Redis = None


class Cache:
    def __init__(self):
        self._data: dict = {}
        self._ttl: dict = {}
        self._redis = None

    async def _get_redis(self):
        if Redis is None:
            return None
        if self._redis is None:
            self._redis = Redis.from_url(settings.REDIS_URL, db=settings.REDIS_DB_CACHE, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
        try:
            await self._redis.ping()
            return self._redis
        except Exception:
            return None

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return f"cache:{prefix}:{hashlib.sha256(key_data.encode()).hexdigest()}"

    async def get(self, key: str) -> Optional[Any]:
        redis = await self._get_redis()
        if redis is not None:
            try:
                raw = await redis.get(key)
                return json.loads(raw) if raw is not None else None
            except Exception:
                redis = None
        if settings.ENVIRONMENT.lower() == "production":
            return None
        if key in self._data:
            if key in self._ttl and self._ttl[key] < datetime.now(timezone.utc):
                self.delete(key)
                return None
            return self._data[key]
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300):
        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.set(key, json.dumps(value, default=str), ex=max(1, ttl_seconds))
                return
            except Exception:
                redis = None
        if settings.ENVIRONMENT.lower() == "production":
            return
        self._data[key] = value
        if ttl_seconds > 0:
            self._ttl[key] = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    async def delete(self, key: str):
        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.delete(key)
                return
            except Exception:
                pass
        self._data.pop(key, None)
        self._ttl.pop(key, None)

    async def clear(self):
        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.flushdb()
                return
            except Exception:
                pass
        self._data.clear()
        self._ttl.clear()


cache = Cache()


def cached(prefix: str, ttl: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = cache._make_key(prefix, *args, **kwargs)
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return {"cached": True, "data": cached_value}
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return {"cached": False, "data": result}
        return wrapper
    return decorator
