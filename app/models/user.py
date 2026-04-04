"""
User model — covers all 3 roles (super_admin, company, portal_user).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserRole
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_constraint=True),
        nullable=False,
    )
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── relationships ────────────────────────────────────────────
    tenant: Mapped[Optional["Tenant"]] = relationship(
        "Tenant",
        foreign_keys=[tenant_id],
        back_populates="users",
        lazy="selectin",
    )
    owned_tenant: Mapped[Optional["Tenant"]] = relationship(
        "Tenant",
        foreign_keys="Tenant.owner_user_id",
        back_populates="owner",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email!r} role={self.role.value}>"
