"""
Cache API v7.4
Redis-based caching для оптимизации запросов
"""

import json
import hashlib
from typing import Optional, Any
from datetime import datetime, timezone, timedelta

from app.core.config import settings


class Cache:
    """Simple in-memory cache (в проде — Redis)"""

    def __init__(self):
        self._data: dict = {}
        self._ttl: dict = {}

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Создание ключа из аргументов"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"

    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if key in self._data:
            if key in self._ttl and self._ttl[key] < datetime.now(timezone.utc):
                del self._data[key]
                del self._ttl[key]
                return None
            return self._data[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Сохранить значение в кэш"""
        self._data[key] = value
        if ttl_seconds > 0:
            self._ttl[key] = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    def delete(self, key: str):
        """Удалить значение из кэша"""
        if key in self._data:
            del self._data[key]
        if key in self._ttl:
            del self._ttl[key]

    def delete_pattern(self, pattern: str):
        """Удалить по паттерну"""
        keys_to_delete = [k for k in self._data.keys() if pattern in k]
        for k in keys_to_delete:
            self.delete(k)

    def clear(self):
        """Очистить весь кэш"""
        self._data.clear()
        self._ttl.clear()

    def get_stats(self) -> dict:
        """Статистика кэша"""
        now = datetime.now(timezone.utc)
        expired = sum(1 for k, v in self._ttl.items() if v < now)
        return {
            "total_keys": len(self._data),
            "expired_keys": expired,
            "active_keys": len(self._data) - expired,
        }


cache = Cache()


def cached(prefix: str, ttl: int = 300):
    """Декоратор для кэширования функций"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Создаём ключ из аргументов
            cache_key = cache._make_key(prefix, *args, **kwargs)

            # Проверяем кэш
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return {"cached": True, "data": cached_value}

            # Вызываем функцию
            result = await func(*args, **kwargs)

            # Сохраняем в кэш
            cache.set(cache_key, result, ttl)

            return {"cached": False, "data": result}
        return wrapper
    return decorator
