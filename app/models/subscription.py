"""
Subscription model — the core business entity.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import SubscriptionStatus
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.subscription_line import SubscriptionLine


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_terms: Mapped[str] = mapped_column(
        String(100), nullable=False, default="net-30"
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(
            SubscriptionStatus,
            name="subscription_status",
            create_constraint=True,
        ),
        default=SubscriptionStatus.DRAFT,
        nullable=False,
    )
    downgrade_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    downgrade_to_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=True,
    )

    # ── relationships ────────────────────────────────────────────
    lines: Mapped[list["SubscriptionLine"]] = relationship(
        "SubscriptionLine", back_populates="subscription", lazy="selectin"
    )

    # UniqueConstraint per tenant handled in migration
    __table_args__ = (
        # Composite unique: subscription number unique within a tenant
        {"info": {"tenant_unique": ("tenant_id", "number")}},
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.number!r} {self.status.value}>"
