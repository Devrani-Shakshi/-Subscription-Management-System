"""
Base model that every SQLAlchemy model inherits from.

Provides:
- UUID primary key
- created_at / deleted_at (soft-delete) timestamps
- soft_delete() / restore() helpers
- to_dict() that auto-strips sensitive fields
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

# Fields that must never leak into API responses
_SENSITIVE_FIELDS: frozenset[str] = frozenset(
    {"password_hash", "refresh_token_hash"}
)


class TimestampMixin:
    """Adds created_at and soft-delete deleted_at to any model."""

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        default=None,
    )


class BaseModel(TimestampMixin, DeclarativeBase):
    """
    Abstract declarative base for the entire schema.

    Every concrete model inherits this and gets:
    - id: UUID PK (auto-generated)
    - created_at, deleted_at
    - soft_delete / restore / to_dict
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ── soft-delete helpers ──────────────────────────────────────
    def soft_delete(self) -> None:
        self.deleted_at = datetime.utcnow()  # type: ignore[assignment]

    def restore(self) -> None:
        self.deleted_at = None  # type: ignore[assignment]

    # ── serialisation ────────────────────────────────────────────
    def to_dict(self, *, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        Return a plain dict of mapped columns, stripping sensitive
        fields automatically (e.g. password_hash).
        """
        skip = _SENSITIVE_FIELDS | (exclude or set())
        result: dict[str, Any] = {}
        for col in self.__table__.columns:
            if col.key in skip:
                continue
            value = getattr(self, col.key)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[col.key] = value
        return result
