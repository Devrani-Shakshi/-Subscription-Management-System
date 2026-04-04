"""
Token family service — Redis-backed refresh token reuse detection.

Each login creates a token "family". On each refresh, the old hash is
replaced. If a hash is reused, the entire family is revoked.
"""

from __future__ import annotations

import uuid

from app.core.redis import get_redis
from app.core.security import hash_token


class TokenFamilyService:
    """Manages refresh-token families in Redis."""

    @staticmethod
    def _key(family_id: uuid.UUID) -> str:
        return f"token_family:{family_id}"

    @staticmethod
    async def register(
        family_id: uuid.UUID,
        refresh_token: str,
        ttl_seconds: int,
    ) -> None:
        """Store hash of a new refresh token in the family set."""
        redis = await get_redis()
        key = TokenFamilyService._key(family_id)
        token_h = hash_token(refresh_token)
        await redis.sadd(key, token_h)
        await redis.expire(key, ttl_seconds)

    @staticmethod
    async def validate_and_rotate(
        family_id: uuid.UUID,
        old_token: str,
        new_token: str,
        ttl_seconds: int,
    ) -> bool:
        """
        Validate old token is in the family, remove it, add new one.

        Returns False on reuse detection (old token not in set),
        which means caller should revoke entire family.
        """
        redis = await get_redis()
        key = TokenFamilyService._key(family_id)
        old_h = hash_token(old_token)

        removed = await redis.srem(key, old_h)
        if not removed:
            # Reuse detected — revoke entire family
            await redis.delete(key)
            return False

        new_h = hash_token(new_token)
        await redis.sadd(key, new_h)
        await redis.expire(key, ttl_seconds)
        return True

    @staticmethod
    async def revoke_family(family_id: uuid.UUID) -> None:
        """Delete entire token family — all sessions revoked."""
        redis = await get_redis()
        await redis.delete(TokenFamilyService._key(family_id))
