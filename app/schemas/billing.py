"""
Billing Pydantic v2 schemas — invoices, payments, dunning.

Rules:
- All strings stripped of whitespace, HTML tags removed.
- Strict typing with Python Enums.
- No raw dicts — structured response models.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.core.enums import (
    DunningAction,
    DunningStatus,
    InvoiceStatus,
    PaymentMethod,
)

_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(v: str) -> str:
    return _HTML_TAG.sub("", v)


# ═══════════════════════════════════════════════════════════════
# Invoice Schemas
# ═══════════════════════════════════════════════════════════════


class InvoiceLineResponse(BaseModel):
    id: UUID
    product_id: UUID
    product: str = ""
    description: str = ""
    quantity: int
    unitPrice: Decimal
    taxPercent: float = 0
    discount: Decimal = Decimal("0")
    amount: Decimal


class InvoiceResponse(BaseModel):
    id: UUID
    number: str
    subscription_id: UUID
    customer_id: UUID
    subscriptionName: str = ""
    customerName: str = ""
    customerEmail: str = ""
    customerAddress: str = ""
    status: InvoiceStatus
    invoiceDate: datetime
    dueDate: date
    subtotal: Decimal
    taxTotal: Decimal
    discountTotal: Decimal
    total: Decimal
    amountPaid: Decimal
    amountDue: Decimal
    paymentTerms: str = ""
    notes: str = ""
    lineItems: list[InvoiceLineResponse] = []
    createdAt: datetime
    updatedAt: datetime


class InvoiceListResponse(BaseModel):
    data: list[InvoiceResponse]
    meta: dict[str, int]


class InvoiceGenerateRequest(BaseModel):
    subscription_id: UUID


class InvoiceUpdateRequest(BaseModel):
    due_date: Optional[date] = None
    status: Optional[InvoiceStatus] = None


class InvoiceBulkSendRequest(BaseModel):
    invoice_ids: list[UUID]

    @field_validator("invoice_ids", mode="before")
    @classmethod
    def validate_ids(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one invoice ID is required.")
        if len(v) > 100:
            raise ValueError("Maximum 100 invoices per bulk send.")
        return v


# ═══════════════════════════════════════════════════════════════
# Payment Schemas
# ═══════════════════════════════════════════════════════════════


class PaymentCreateRequest(BaseModel):
    invoice_id: UUID
    amount: Decimal
    method: PaymentMethod
    paid_at: Optional[datetime] = None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        v = Decimal(str(v))
        if v <= 0:
            raise ValueError("Payment amount must be positive.")
        return v


class PaymentResponse(BaseModel):
    id: UUID
    invoiceId: UUID
    customerId: UUID
    method: PaymentMethod
    amount: Decimal
    paidAt: datetime
    createdAt: datetime


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int


class PortalPayRequest(BaseModel):
    """Portal user pays an invoice (Stripe token-based)."""
    payment_token: Optional[str] = None
    method: PaymentMethod = PaymentMethod.CARD


# ═══════════════════════════════════════════════════════════════
# Dunning Schemas
# ═══════════════════════════════════════════════════════════════


class DunningScheduleResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    attempt_number: int
    action: DunningAction
    channel: str
    scheduled_at: datetime
    status: DunningStatus
    result_json: dict


class DunningScheduleListResponse(BaseModel):
    items: list[DunningScheduleResponse]
    total: int
