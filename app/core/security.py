"""
Security utilities — password hashing, JWT encode/decode, token helpers.

Single responsibility: cryptographic operations only.
No DB, no request context, no business rules.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ─────────────────────────────────────────────
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Bcrypt-hash a plain-text password."""
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain against bcrypt hash."""
    return _pwd_ctx.verify(plain, hashed)


# ── JWT ──────────────────────────────────────────────────────────
def create_access_token(
    *,
    user_id: uuid.UUID,
    role: str,
    tenant_id: Optional[uuid.UUID],
    email: str,
) -> str:
    """Create a short-lived access JWT."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    *,
    user_id: uuid.UUID,
    family_id: uuid.UUID,
) -> str:
    """Create a long-lived refresh JWT."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "family_id": str(family_id),
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT. Raises JWTError on failure."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ── Token hashing (for DB storage) ──────────────────────────────
def hash_token(token: str) -> str:
    """SHA-256 hash a token for safe DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Invite token generation ─────────────────────────────────────
def generate_invite_token() -> str:
    """Generate a URL-safe random invite token."""
    return secrets.token_urlsafe(48)
