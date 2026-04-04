"""
Redis client singleton.

Used for:
- Rate limiting (sliding window counters)
- Token family tracking (refresh token reuse detection)
"""

from __future__ import annotations

from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Return (or create) an async Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def close_redis() -> None:
    """Graceful shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()  # type: ignore[union-attr]
        _pool = None
