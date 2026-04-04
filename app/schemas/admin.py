"""
Admin Pydantic v2 schemas — super_admin endpoints.

Covers:
- Company CRUD (create / list / detail / suspend / reactivate / delete)
- Platform dashboard (metrics, breakdown, alerts)
- Audit log (list, export)
- Revenue chart data
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.enums import AuditAction, TenantStatus


# ── Helpers ──────────────────────────────────────────────────────
_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(v: str) -> str:
    return _HTML_TAG.sub("", v)


# ═══════════════════════════════════════════════════════════════
# Company Schemas
# ═══════════════════════════════════════════════════════════════

class CreateCompanySchema(BaseModel):
    """Create a new tenant + company user."""
    name: str
    slug: str
    email: EmailStr

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = _strip_html(v.strip())
        if len(v) < 2:
            raise ValueError("Company name must be at least 2 characters.")
        return v

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = _strip_html(v.strip().lower())
        if not re.match(r"^[a-z0-9\-]{2,63}$", v):
            raise ValueError(
                "Slug must be 2–63 chars, lowercase alphanumeric and hyphens only."
            )
        return v

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return _strip_html(v.strip().lower())


class SlugCheckResponse(BaseModel):
    """Response for slug uniqueness check."""
    available: bool
    suggestion: Optional[str] = None


class TenantListItem(BaseModel):
    """Single row in the company list."""
    id: UUID
    name: str
    slug: str
    status: TenantStatus
    mrr: Decimal = Decimal("0.00")
    active_subs_count: int = 0
    trial_ends_at: Optional[datetime] = None
    created_at: datetime


class TenantListResponse(BaseModel):
    """Paginated company list."""
    items: list[TenantListItem]
    total: int
    page: int
    page_size: int


class TenantDetailResponse(BaseModel):
    """Full tenant detail with tab data."""
    id: UUID
    name: str
    slug: str
    status: TenantStatus
    owner_email: Optional[str] = None
    owner_name: Optional[str] = None
    mrr: Decimal = Decimal("0.00")
    active_subs_count: int = 0
    total_customers: int = 0
    total_invoices: int = 0
    trial_ends_at: Optional[datetime] = None
    created_at: datetime


class CompanyCreateResponse(BaseModel):
    """Response after creating a company."""
    tenant_id: UUID
    name: str
    slug: str
    invite_url: str
    invite_token: str


class SuspendReactivateResponse(BaseModel):
    """Response after suspend/reactivate."""
    tenant_id: UUID
    status: TenantStatus
    message: str


class DeleteCompanyResponse(BaseModel):
    """Response after soft-deleting a company."""
    tenant_id: UUID
    message: str


# ═══════════════════════════════════════════════════════════════
# Dashboard Schemas
# ═══════════════════════════════════════════════════════════════

class MetricCard(BaseModel):
    """Single KPI card on the dashboard."""
    label: str
    value: str
    delta: Optional[str] = None
    trend: Optional[Literal["up", "down", "flat"]] = None


class CompanyBreakdownRow(BaseModel):
    """Row in the company breakdown table."""
    tenant_id: UUID
    name: str
    status: TenantStatus
    mrr: Decimal
    active_subs: int
    customers: int


class AlertItem(BaseModel):
    """Platform alert item."""
    severity: Literal["info", "warning", "error"]
    message: str
    tenant_id: Optional[UUID] = None
    tenant_name: Optional[str] = None


class PlatformDashboardResponse(BaseModel):
    """Aggregated platform-wide dashboard."""
    metrics: list[MetricCard]
    company_breakdown: list[CompanyBreakdownRow]
    alerts: list[AlertItem]


# ═══════════════════════════════════════════════════════════════
# Audit Log Schemas
# ═══════════════════════════════════════════════════════════════

class AuditLogFilter(BaseModel):
    """Query params for filtering audit log."""
    tenant_id: Optional[UUID] = None
    actor_id: Optional[UUID] = None
    entity_type: Optional[str] = None
    action: Optional[AuditAction] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class AuditLogItem(BaseModel):
    """Single audit log entry."""
    id: UUID
    tenant_id: Optional[UUID] = None
    tenant_name: Optional[str] = None
    actor_id: UUID
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    actor_role: str
    entity_type: str
    entity_id: UUID
    action: AuditAction
    diff_json: dict[str, Any]
    created_at: datetime


class AuditLogResponse(BaseModel):
    """Paginated audit log."""
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════
# Revenue Schemas
# ═══════════════════════════════════════════════════════════════

class RevenueDataPoint(BaseModel):
    """Single data point in the revenue chart."""
    month: str
    revenue: Decimal
    tenant_count: int


class RevenueChartResponse(BaseModel):
    """Cross-tenant revenue chart data."""
    data_points: list[RevenueDataPoint]
    total_revenue: Decimal
    period: str
