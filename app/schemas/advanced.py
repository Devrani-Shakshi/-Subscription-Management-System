"""
Schemas for advanced modules — Churn, Revenue, Metrics, Bulk, Audit (company-scoped).

All schemas use Pydantic v2 with strict typing.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import (
    AuditAction,
    BulkJobStatus,
    BulkOperationType,
    ChurnRiskLevel,
)

_HTML_TAG = re.compile(r"<[^>]+>")


def _sanitize(v: str) -> str:
    return _HTML_TAG.sub("", v.strip())


# ═══════════════════════════════════════════════════════════════
# Churn Schemas
# ═══════════════════════════════════════════════════════════════


class ChurnSignalBreakdown(BaseModel):
    """Single signal in the churn score breakdown."""

    key: str
    weight: int
    triggered: bool
    detail: str = ""


class ChurnScoreItem(BaseModel):
    """Single churn score entry."""

    id: UUID
    customer_id: UUID
    customer_name: str
    customer_email: str
    score: int
    risk_level: ChurnRiskLevel
    signals: list[dict[str, Any]] = []
    computed_at: datetime


class ChurnScoreListResponse(BaseModel):
    """Paginated churn score list."""

    items: list[ChurnScoreItem]
    total: int


# ═══════════════════════════════════════════════════════════════
# Revenue Recognition Schemas
# ═══════════════════════════════════════════════════════════════


class RevenueTimelineItem(BaseModel):
    """Single month in the revenue timeline."""

    month: str
    recognized: str
    deferred: str = "0"
    cumulative: str


class RevenueTimelineResponse(BaseModel):
    """Revenue recognition timeline."""

    timeline: list[RevenueTimelineItem]
    total_recognized: str = "0"


class CrossTenantRevenueItem(BaseModel):
    """Revenue item with tenant count (admin view)."""

    month: str
    recognized: str
    cumulative: str
    tenant_count: int = 0


class CrossTenantRevenueResponse(BaseModel):
    """Cross-tenant revenue timeline (admin)."""

    timeline: list[CrossTenantRevenueItem]


# ═══════════════════════════════════════════════════════════════
# Health Dashboard Schemas
# ═══════════════════════════════════════════════════════════════


class MetricItem(BaseModel):
    """Single metric on the dashboard."""

    name: str
    value: str
    raw_value: str = "0"
    trend: str = "flat"
    delta: str = ""
    period: str = ""


class CompanyDashboardResponse(BaseModel):
    """Company health dashboard."""

    metrics: dict[str, MetricItem]


# ═══════════════════════════════════════════════════════════════
# Audit Schemas (company-scoped)
# ═══════════════════════════════════════════════════════════════


class CompanyAuditLogFilter(BaseModel):
    """Filter params for company audit log."""

    entity_type: Optional[str] = None
    action: Optional[AuditAction] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class CompanyAuditLogItem(BaseModel):
    """Single audit log entry (company view)."""

    id: UUID
    actor_id: UUID
    actor_name: Optional[str] = None
    actor_role: str
    entity_type: str
    entity_id: UUID
    action: AuditAction
    diff_json: dict[str, Any]
    created_at: datetime


class CompanyAuditLogResponse(BaseModel):
    """Paginated company audit log."""

    items: list[CompanyAuditLogItem]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════
# Bulk Operation Schemas
# ═══════════════════════════════════════════════════════════════


class BulkOperationRequest(BaseModel):
    """Request to execute a bulk operation."""

    operation: BulkOperationType
    subscription_ids: list[UUID] = Field(..., min_length=1, max_length=500)
    params: dict[str, Any] = Field(default_factory=dict)
    skip_ids: list[UUID] = Field(default_factory=list)
    confirm: bool = False  # If False, just preview conflicts


class BulkConflictItem(BaseModel):
    """Single conflict in preview."""

    id: str
    conflict_type: str
    reason: str


class BulkPreviewResponse(BaseModel):
    """Preview of bulk operation conflicts."""

    total: int
    clean_count: int
    conflict_count: int
    conflicts: list[BulkConflictItem]


class BulkFailedItem(BaseModel):
    """Failed item in bulk result."""

    id: str
    reason: str


class BulkOperationResponse(BaseModel):
    """Result of a bulk operation execution."""

    success: list[str]
    failed: list[BulkFailedItem]
    conflicts: list[BulkConflictItem]
    total: int
    success_count: int
    failed_count: int


class BulkJobStatusResponse(BaseModel):
    """Status of an async bulk job."""

    status: BulkJobStatus
    progress: int = 0
    result: Optional[BulkOperationResponse] = None
