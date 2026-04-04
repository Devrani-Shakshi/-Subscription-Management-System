"""
Revenue recognition model — tracks recognized revenue over periods.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RevenueRecognition(BaseModel):
    __tablename__ = "revenue_recognition"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )
    recognized_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    recognition_date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<RevenueRecognition {self.period} "
            f"amount={self.recognized_amount}>"
        )
