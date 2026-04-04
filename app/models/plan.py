"""
Plan model — subscription plans with billing period, features, and flags.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import BillingPeriod
from app.models.base import BaseModel

_DEFAULT_FLAGS: dict[str, Any] = {
    "auto_close": False,
    "closable": True,
    "pausable": False,
    "renewable": True,
}


class Plan(BaseModel):
    __tablename__ = "plans"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    billing_period: Mapped[BillingPeriod] = mapped_column(
        SAEnum(BillingPeriod, name="billing_period", create_constraint=True),
        nullable=False,
    )
    min_qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    features_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    flags_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=lambda: dict(_DEFAULT_FLAGS)
    )

    def __repr__(self) -> str:
        return f"<Plan {self.name!r} {self.billing_period.value}>"
