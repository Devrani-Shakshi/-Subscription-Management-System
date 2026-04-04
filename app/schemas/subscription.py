"""
Subscription Pydantic v2 schemas — strict validation.

Rules:
- All strings stripped + HTML-sanitized.
- Enums from core.enums — never raw strings.
- Decimal fields use condecimal for range enforcement.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import SubscriptionStatus

_HTML_TAG = re.compile(r"<[^>]+>")


def _sanitize(v: str) -> str:
    return _HTML_TAG.sub("", v.strip())


# ═══════════════════════════════════════════════════════════════
# Subscription Line schemas
# ═══════════════════════════════════════════════════════════════

class SubscriptionLineCreate(BaseModel):
    product_id: UUID
    qty: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    tax_ids: Optional[list[UUID]] = None


class SubscriptionLineResponse(BaseModel):
    id: UUID
    product_id: UUID
    qty: int
    unit_price: Decimal
    tax_ids: Optional[list[UUID]] = None
    created_at: str

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Subscription Create (wizard step 5)
# ═══════════════════════════════════════════════════════════════

class SubscriptionCreate(BaseModel):
    customer_id: UUID
    plan_id: UUID
    start_date: date
    expiry_date: date
    payment_terms: str = Field(
        default="net-30", min_length=1, max_length=100
    )
    lines: list[SubscriptionLineCreate] = Field(..., min_length=1)

    @field_validator("payment_terms", mode="before")
    @classmethod
    def sanitize_terms(cls, v: str) -> str:
        return _sanitize(v)

    @model_validator(mode="after")
    def end_after_start(self) -> "SubscriptionCreate":
        if self.expiry_date <= self.start_date:
            raise ValueError("expiry_date must be after start_date.")
        return self


# ═══════════════════════════════════════════════════════════════
# Subscription Update (PATCH)
# ═══════════════════════════════════════════════════════════════

class SubscriptionUpdate(BaseModel):
    payment_terms: Optional[str] = Field(
        None, min_length=1, max_length=100
    )
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None

    @field_validator("payment_terms", mode="before")
    @classmethod
    def sanitize_terms(cls, v: str | None) -> str | None:
        return _sanitize(v) if v is not None else None


# ═══════════════════════════════════════════════════════════════
# Action schemas
# ═══════════════════════════════════════════════════════════════

class UpgradeRequest(BaseModel):
    new_plan_id: UUID


class DowngradeRequest(BaseModel):
    new_plan_id: UUID


class ChangePlanRequest(BaseModel):
    plan_id: UUID


class CancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def sanitize_reason(cls, v: str | None) -> str | None:
        return _sanitize(v) if v is not None else None


# ═══════════════════════════════════════════════════════════════
# Bulk create
# ═══════════════════════════════════════════════════════════════

class BulkSubscriptionCreate(BaseModel):
    items: list[SubscriptionCreate] = Field(..., min_length=1, max_length=50)


# ═══════════════════════════════════════════════════════════════
# Response schemas
# ═══════════════════════════════════════════════════════════════

class SubscriptionResponse(BaseModel):
    id: UUID
    number: str
    customer_id: UUID
    plan_id: UUID
    start_date: date
    expiry_date: date
    payment_terms: str
    status: SubscriptionStatus
    downgrade_at: Optional[str] = None
    downgrade_to_plan_id: Optional[UUID] = None
    created_at: str

    model_config = {"from_attributes": True}


class SubscriptionDetailResponse(SubscriptionResponse):
    lines: list[SubscriptionLineResponse] = []


class ChangePlanPreviewResponse(BaseModel):
    direction: str  # 'upgrade' | 'downgrade'
    amount_due_today: str
    pro_rata_days: int
    effective_date: str


class PortalSubscriptionResponse(BaseModel):
    subscription: dict[str, Any]
    plan: dict[str, Any]
    lines: list[dict[str, Any]]
    recent_invoices: list[dict[str, Any]]
