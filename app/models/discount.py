"""
Discount model — fixed or percentage discounts with usage limits.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import DiscountAppliesTo, DiscountType
from app.models.base import BaseModel


class Discount(BaseModel):
    __tablename__ = "discounts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[DiscountType] = mapped_column(
        SAEnum(
            DiscountType,
            name="discount_type",
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_purchase: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    min_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    applies_to: Mapped[DiscountAppliesTo] = mapped_column(
        SAEnum(
            DiscountAppliesTo,
            name="discount_applies_to",
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Discount {self.name!r} {self.type.value}={self.value}>"
