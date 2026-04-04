"""
Tenant model — each company account is a tenant.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import TenantStatus
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Tenant(BaseModel):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", use_alter=True, name="fk_tenants_owner_user"),
        nullable=True,
    )
    status: Mapped[TenantStatus] = mapped_column(
        SAEnum(TenantStatus, name="tenant_status", create_constraint=True),
        default=TenantStatus.TRIAL,
        nullable=False,
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # ── relationships ────────────────────────────────────────────
    owner: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[owner_user_id],
        back_populates="owned_tenant",
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        foreign_keys="User.tenant_id",
        back_populates="tenant",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.slug!r} ({self.status.value})>"
