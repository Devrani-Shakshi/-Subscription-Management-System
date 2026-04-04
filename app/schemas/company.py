"""
Company Pydantic v2 schemas — strict validation for all company CRUD.

Rules:
- All strings stripped + HTML-sanitized.
- Emails lower-cased.
- Decimal fields use condecimal for range enforcement.
- Enums from core.enums — never raw strings.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.enums import BillingPeriod, DiscountAppliesTo, DiscountType

_HTML_TAG = re.compile(r"<[^>]+>")


def _sanitize(v: str) -> str:
    return _HTML_TAG.sub("", v.strip())


# ═══════════════════════════════════════════════════════════════
# Product
# ═══════════════════════════════════════════════════════════════

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)
    sales_price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    cost_price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)

    @field_validator("name", "type", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        return _sanitize(v)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    sales_price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    cost_price: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)

    @field_validator("name", "type", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        return _sanitize(v) if v is not None else None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    type: str
    sales_price: Decimal
    cost_price: Decimal
    variants_count: int = 0
    created_at: str

    model_config = {"from_attributes": True}


class ProductDetailResponse(ProductResponse):
    variants: list[VariantResponse] = []


# ── Variants ─────────────────────────────────────────────────────

class VariantCreate(BaseModel):
    attribute: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=255)
    extra_price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)

    @field_validator("attribute", "value", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        return _sanitize(v)


class VariantResponse(BaseModel):
    id: UUID
    product_id: UUID
    attribute: str
    value: str
    extra_price: Decimal
    created_at: str

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Plan
# ═══════════════════════════════════════════════════════════════

_DEFAULT_FLAGS: dict[str, bool] = {
    "auto_close": False,
    "closable": True,
    "pausable": False,
    "renewable": True,
}


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    billing_period: BillingPeriod
    min_qty: int = Field(default=1, ge=1)
    start_date: date
    end_date: Optional[date] = None
    features_json: dict[str, Any] = Field(default_factory=dict)
    flags_json: dict[str, Any] = Field(default_factory=lambda: dict(_DEFAULT_FLAGS))

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return _sanitize(v)

    @model_validator(mode="after")
    def end_after_start(self) -> "PlanCreate":
        if self.end_date is not None and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        return self


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    billing_period: Optional[BillingPeriod] = None
    min_qty: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    features_json: Optional[dict[str, Any]] = None
    flags_json: Optional[dict[str, Any]] = None

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str | None) -> str | None:
        return _sanitize(v) if v is not None else None


class PlanResponse(BaseModel):
    id: UUID
    name: str
    price: Decimal
    billing_period: BillingPeriod
    min_qty: int
    start_date: date
    end_date: Optional[date] = None
    features_json: dict[str, Any]
    flags_json: dict[str, Any]
    created_at: str

    model_config = {"from_attributes": True}


class PlanPreviewResponse(BaseModel):
    """Data for rendering a plan card as the customer sees it."""
    id: UUID
    name: str
    price: Decimal
    billing_period: BillingPeriod
    features: dict[str, Any]
    flags: dict[str, Any]


# ═══════════════════════════════════════════════════════════════
# Discount
# ═══════════════════════════════════════════════════════════════

class DiscountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: DiscountType
    value: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    min_purchase: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    min_qty: int = Field(default=1, ge=1)
    start_date: date
    end_date: date
    usage_limit: Optional[int] = Field(None, gt=0)
    applies_to: DiscountAppliesTo

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return _sanitize(v)

    @model_validator(mode="after")
    def end_after_start(self) -> "DiscountCreate":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        return self

    @model_validator(mode="after")
    def percent_max_100(self) -> "DiscountCreate":
        if self.type == DiscountType.PERCENT and self.value > 100:
            raise ValueError("Percentage discount cannot exceed 100.")
        return self


class DiscountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[DiscountType] = None
    value: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    min_purchase: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    min_qty: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = Field(None, gt=0)
    applies_to: Optional[DiscountAppliesTo] = None

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str | None) -> str | None:
        return _sanitize(v) if v is not None else None


class DiscountResponse(BaseModel):
    id: UUID
    name: str
    type: DiscountType
    value: Decimal
    min_purchase: Decimal
    min_qty: int
    start_date: date
    end_date: date
    usage_limit: Optional[int] = None
    used_count: int
    applies_to: DiscountAppliesTo
    created_at: str

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Tax
# ═══════════════════════════════════════════════════════════════

class TaxCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rate: Decimal = Field(..., ge=0, le=100, max_digits=5, decimal_places=2)
    type: str = Field(..., min_length=1, max_length=50)

    @field_validator("name", "type", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        return _sanitize(v)


class TaxUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate: Optional[Decimal] = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    type: Optional[str] = Field(None, min_length=1, max_length=50)

    @field_validator("name", "type", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str | None) -> str | None:
        return _sanitize(v) if v is not None else None


class TaxResponse(BaseModel):
    id: UUID
    name: str
    rate: Decimal
    type: str
    created_at: str

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Quotation Template
# ═══════════════════════════════════════════════════════════════

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    validity_days: int = Field(default=30, ge=1)
    plan_id: UUID

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return _sanitize(v)


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    validity_days: Optional[int] = Field(None, ge=1)
    plan_id: Optional[UUID] = None

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str | None) -> str | None:
        return _sanitize(v) if v is not None else None


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    validity_days: int
    plan_id: UUID
    created_at: str

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════
# Customer (read-only views for company)
# ═══════════════════════════════════════════════════════════════

class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    created_at: str

    model_config = {"from_attributes": True}


class CustomerDetailResponse(CustomerResponse):
    """Extended detail with subscription + invoice history."""
    subscription_status: Optional[str] = None
    plan_name: Optional[str] = None
    churn_score: Optional[float] = None


# ── Invite ───────────────────────────────────────────────────────

class CustomerInviteSchema(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return _sanitize(v.lower())


# ═══════════════════════════════════════════════════════════════
# Pagination wrapper
# ═══════════════════════════════════════════════════════════════

class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    offset: int
    limit: int


# Forward-ref update for ProductDetailResponse
ProductDetailResponse.model_rebuild()
