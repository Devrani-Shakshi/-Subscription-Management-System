"""
Invoice model — financial document tied to subscriptions.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InvoiceStatus
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.invoice_line import InvoiceLine
    from app.models.payment import Payment


class Invoice(BaseModel):
    __tablename__ = "invoices"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    discount_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("discounts.id"),
        nullable=True,
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(
            InvoiceStatus, name="invoice_status", create_constraint=True
        ),
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    tax_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    discount_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    # ── relationships ────────────────────────────────────────────
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine", back_populates="invoice", lazy="selectin"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="invoice", lazy="selectin"
    )

    @property
    def amount_due(self) -> Decimal:
        """Outstanding balance."""
        return self.total - self.amount_paid

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} {self.status.value}>"
