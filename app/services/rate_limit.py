"""
Rate limiting service — Redis sliding window.

Patterns:
  login:         5 attempts / 10 min per email  +  20 / 10 min per IP
  reset-request: 3 / hour per email
  refresh:       10 / min per user
  authenticated: 300 / min per user
"""

from __future__ import annotations

from app.core.redis import get_redis
from app.exceptions.base import RateLimitException


class RateLimitService:
    """Sliding-window rate limiter backed by Redis."""

    @staticmethod
    async def check(
        *,
        key: str,
        max_attempts: int,
        window_seconds: int,
    ) -> None:
        """
        Increment counter for *key*. Raise 429 if over limit.

        Redis key: ``rl:{key}`` with TTL = window_seconds.
        """
        redis = await get_redis()
        rk = f"rl:{key}"
        current = await redis.incr(rk)
        if current == 1:
            await redis.expire(rk, window_seconds)
        if current > max_attempts:
            ttl = await redis.ttl(rk)
            raise RateLimitException(
                f"Too many requests. Retry after {ttl}s.",
                extra={"retry_after": ttl},
            )

    @staticmethod
    async def check_login_email(email: str) -> None:
        await RateLimitService.check(
            key=f"login:email:{email}", max_attempts=5, window_seconds=600
        )

    @staticmethod
    async def check_login_ip(ip: str) -> None:
        await RateLimitService.check(
            key=f"login:ip:{ip}", max_attempts=20, window_seconds=600
        )

    @staticmethod
    async def check_reset_email(email: str) -> None:
        await RateLimitService.check(
            key=f"reset:email:{email}", max_attempts=3, window_seconds=3600
        )

    @staticmethod
    async def check_refresh(user_id: str) -> None:
        await RateLimitService.check(
            key=f"refresh:user:{user_id}", max_attempts=10, window_seconds=60
        )

    @staticmethod
    async def check_authenticated(user_id: str) -> None:
        await RateLimitService.check(
            key=f"auth:user:{user_id}", max_attempts=300, window_seconds=60
        )
