import datetime
import json

from django.conf import settings
from django.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT
from django.core.cache import caches
from asgiref.sync import sync_to_async


class DualCacheBackend(BaseCache):
    """
    Кастомный кэш, объединяющий два стандартных backend’а:
    - Redis для быстрого доступа с коротким timeout (например, 1 час).
    - Файловый кэш для долговременного хранения (например, 3 дня).
    
    Настройки backend’а передаются через OPTIONS в настройках CACHES.
    """
    def __init__(self, location, params):
        super().__init__(params)
        options = params.get('OPTIONS', {})
        # Алиас для Redis-кэша (быстрый)
        self.redis_alias = options.get('REDIS_CACHE_ALIAS', 'redis')
        # Алиас для локального кэша (например, файловый кэш)
        self.local_alias = options.get('LOCAL_CACHE_ALIAS', 'local')
        self.redis_cache = caches[self.redis_alias]
        self.local_cache = caches[self.local_alias]
        # Таймауты: для Redis – короткий, для локального – долговременный
        self.redis_timeout = options.get('REDIS_TIMEOUT', 3600)  # 1 час по умолчанию
        self.local_timeout = options.get('LOCAL_TIMEOUT', 3 * 24 * 3600)  # 3 дня по умолчанию

    def _log(self, action, key, value=None, extra=""):
        if settings.DEBUG:
            size = len(str(value)) if value is not None else 0
            print(f"[📝]Cache: {action} - key: {key}, size: {size}. {extra}\n └value = {str(value)[:20]}")

    def get(self, key, default=None, version=None):
        # Сначала ищем значение в Redis
        value = self.redis_cache.get(key, default=None)
        self._log("get Redis", key, value, "Found in Redis" if value is not None else "Not found in Redis")
        if value is not None:
            return value

        # Если не найдено в Redis, ищем в локальном кэше (файловом)
        value = self.local_cache.get(key, default=None)
        self._log("get Local", key, value, "Found in Local Cache" if value is not None else "Not found in Local Cache")
        if value is not None:
            # Если значение найдено в локальном кэше, репопулируем Redis для ускорения доступа
            self.redis_cache.set(key, value, timeout=self.redis_timeout)
            return value

        return default

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, store_local=True, version=None):
        # Используем переданный timeout для Redis, если он задан, иначе значение по умолчанию
        redis_timeout = timeout if timeout is not DEFAULT_TIMEOUT else self.redis_timeout
        self.redis_cache.set(key, value, timeout=redis_timeout)
        self._log("set Redis", key, value, f"Timeout: {redis_timeout}")
        if store_local:
            # Для локального кэша всегда используем более длительный период хранения
            self.local_cache.set(key, value, timeout=self.local_timeout)
            self._log("set Local", key, value, f"Timeout: {self.local_timeout}")
        return True

    def delete(self, key, version=None):
        self.redis_cache.delete(key)
        self._log("delete Redis", key, extra="Deleted from Redis")
        self.local_cache.delete(key)
        self._log("delete Local", key, extra="Deleted from Local Cache")
        return True
    
    def clear(self):
        self.redis_cache.clear()
        self._log("clear", "all keys", extra="Redis cache cleared")
        self.local_cache.clear()
        self._log("clear", "all keys", extra="Local cache cleared")
        
    # Асинхронные аналоги методов

    async def aget(self, key, default=None, version=None):
        value = await sync_to_async(self.redis_cache.get)(key, default=None)
        self._log("aget Redis", key, value, "Found in Redis" if value is not None else "Not found in Redis")

        if value is not None:
            #await sync_to_async(self.redis_cache.set)(key, value, timeout=self.redis_timeout)
            return value
        
        value = await sync_to_async(self.local_cache.get)(key, default=None)
        self._log("aget Local", key, value, "Found in Local Cache" if value is not None else "Not found in Local Cache")

        if value is not None:
            await sync_to_async(self.redis_cache.set)(key, value, timeout=self.redis_timeout)
            return value

        return default

    async def aset(self, key, value, timeout=DEFAULT_TIMEOUT, store_local=True, version=None) :
        redis_timeout = timeout if timeout is not DEFAULT_TIMEOUT else self.redis_timeout
        await sync_to_async(self.redis_cache.set)(key, value, timeout=redis_timeout)
        self._log("aset Redis", key, value, f"Timeout: {redis_timeout}")
        if store_local:
            await sync_to_async(self.local_cache.set)(key, value, timeout=self.local_timeout)
            self._log("aset Local", key, value, f"Timeout: {self.local_timeout}")
        return True
