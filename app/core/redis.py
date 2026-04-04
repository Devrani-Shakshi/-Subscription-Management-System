"""
Redis client singleton.

Used for:
- Rate limiting (sliding window counters)
- Token family tracking (refresh token reuse detection)
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Set

import redis.asyncio as aioredis
from redis.exceptions import ConnectionError

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[aioredis.Redis | DummyRedis] = None


class DummyRedis:
    """In-memory fallback when real Redis is unavailable (development only)."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._sets: dict[str, Set[str]] = {}

    async def sadd(self, key: str, *values: str) -> int:
        if key not in self._sets:
            self._sets[key] = set()
        added = 0
        for v in values:
            if v not in self._sets[key]:
                self._sets[key].add(v)
                added += 1
        return added

    async def srem(self, key: str, *values: str) -> int:
        if key not in self._sets:
            return 0
        removed = 0
        for v in values:
            if v in self._sets[key]:
                self._sets[key].remove(v)
                removed += 1
        return removed

    async def expire(self, key: str, seconds: int) -> bool:
        return True

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                deleted += 1
            if k in self._sets:
                del self._sets[k]
                deleted += 1
        return deleted

    async def incr(self, key: str) -> int:
        val = self._data.get(key, 0) + 1
        self._data[key] = val
        return val

    async def ttl(self, key: str) -> int:
        return 60  # Mock TTL

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        pass


async def get_redis() -> aioredis.Redis | DummyRedis:
    """Return an async Redis connection pool, falling back to DummyRedis if unavailable."""
    global _pool
    if _pool is None:
        try:
            # Short timeout to avoid long hangs if redis is down
            _pool = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=20,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
            # Ping to verify connection actually works
            await _pool.ping()
            logger.info("Connected to Redis at %s", settings.REDIS_URL)
        except (ConnectionError, Exception) as e:
            logger.warning(
                "Could not connect to Redis (%s). Falling back to in-memory DummyRedis.", 
                str(e)
            )
            _pool = DummyRedis()
    return _pool


async def close_redis() -> None:
    """Graceful shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
