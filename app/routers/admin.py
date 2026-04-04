"""
Admin router — super_admin only.

All routes guarded by Depends(require_super_admin) at router level.
Business logic delegated entirely to service layer.

Routes:
  GET    /admin/companies                     → list all tenants
  POST   /admin/companies                     → create tenant + company user
  GET    /admin/companies/check-slug          → slug uniqueness check
  GET    /admin/companies/{tenant_id}         → single tenant detail
  PATCH  /admin/companies/{tenant_id}/suspend → suspend
  PATCH  /admin/companies/{tenant_id}/reactivate → reactivate
  DELETE /admin/companies/{tenant_id}         → soft-delete
  GET    /admin/dashboard                     → platform metrics
  GET    /admin/audit                         → audit log (filterable)
  GET    /admin/audit/export                  → CSV download
  GET    /admin/revenue                       → revenue chart data
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditAction
from app.dependencies.guards import get_tenant_session, require_super_admin
from app.schemas.admin import (
    AuditLogFilter,
    AuditLogResponse,
    CompanyCreateResponse,
    CreateCompanySchema,
    DeleteCompanyResponse,
    PlatformDashboardResponse,
    RevenueChartResponse,
    SlugCheckResponse,
    SuspendReactivateResponse,
    TenantDetailResponse,
    TenantListResponse,
)
from app.schemas.auth import TokenPayload
from app.services.admin_audit import SuperAdminAuditService
from app.services.admin_dashboard import SuperAdminDashboardService
from app.services.admin_tenant import SuperAdminTenantService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_super_admin)],
)


# ── Company CRUD ─────────────────────────────────────────────────

@router.get("/companies", response_model=TenantListResponse)
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantListResponse:
    """List all company tenants with stats."""
    svc = SuperAdminTenantService(db)
    return await svc.list_companies(
        page=page, page_size=page_size, status=status, search=search
    )


@router.post(
    "/companies", status_code=201, response_model=CompanyCreateResponse
)
async def create_company(
    body: CreateCompanySchema,
    user: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_tenant_session),
) -> CompanyCreateResponse:
    """Create a new company tenant and generate invite."""
    svc = SuperAdminTenantService(db)
    return await svc.create_company(body, actor_id=user.user_id)


@router.get(
    "/companies/check-slug", response_model=SlugCheckResponse
)
async def check_slug(
    slug: str = Query(..., min_length=2, max_length=63),
    db: AsyncSession = Depends(get_tenant_session),
) -> SlugCheckResponse:
    """Check slug availability with suggestion."""
    svc = SuperAdminTenantService(db)
    return await svc.check_slug(slug)


@router.get(
    "/companies/{tenant_id}", response_model=TenantDetailResponse
)
async def get_company(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_tenant_session),
) -> TenantDetailResponse:
    """Get full tenant detail."""
    svc = SuperAdminTenantService(db)
    return await svc.get_company_detail(tenant_id)


@router.patch(
    "/companies/{tenant_id}/suspend",
    response_model=SuspendReactivateResponse,
)
async def suspend_company(
    tenant_id: UUID,
    user: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_tenant_session),
) -> SuspendReactivateResponse:
    """Suspend a company tenant."""
    svc = SuperAdminTenantService(db)
    return await svc.suspend_company(tenant_id, actor_id=user.user_id)


@router.patch(
    "/companies/{tenant_id}/reactivate",
    response_model=SuspendReactivateResponse,
)
async def reactivate_company(
    tenant_id: UUID,
    user: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_tenant_session),
) -> SuspendReactivateResponse:
    """Reactivate a suspended company tenant."""
    svc = SuperAdminTenantService(db)
    return await svc.reactivate_company(tenant_id, actor_id=user.user_id)


@router.delete(
    "/companies/{tenant_id}", response_model=DeleteCompanyResponse
)
async def delete_company(
    tenant_id: UUID,
    user: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_tenant_session),
) -> DeleteCompanyResponse:
    """Soft-delete a company (blocked if active subs exist)."""
    svc = SuperAdminTenantService(db)
    return await svc.delete_company(tenant_id, actor_id=user.user_id)


# ── Dashboard ────────────────────────────────────────────────────

@router.get("/dashboard", response_model=PlatformDashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_tenant_session),
) -> PlatformDashboardResponse:
    """Platform-wide metrics dashboard."""
    svc = SuperAdminDashboardService(db)
    return await svc.get_platform_metrics()


# ── Revenue ──────────────────────────────────────────────────────

@router.get("/revenue", response_model=RevenueChartResponse)
async def get_revenue(
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_tenant_session),
) -> RevenueChartResponse:
    """Cross-tenant revenue chart data."""
    svc = SuperAdminDashboardService(db)
    return await svc.get_revenue_chart(months=months)


# ── Audit Log ────────────────────────────────────────────────────

@router.get("/audit", response_model=AuditLogResponse)
async def list_audit_logs(
    tenant_id: Optional[UUID] = Query(None),
    actor_id: Optional[UUID] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[AuditAction] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_tenant_session),
) -> AuditLogResponse:
    """Filterable cross-tenant audit log."""
    filters = AuditLogFilter(
        tenant_id=tenant_id,
        actor_id=actor_id,
        entity_type=entity_type,
        action=action,
        page=page,
        page_size=page_size,
    )
    svc = SuperAdminAuditService(db)
    return await svc.list_audit_logs(filters)


@router.get("/audit/export")
async def export_audit_csv(
    tenant_id: Optional[UUID] = Query(None),
    actor_id: Optional[UUID] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[AuditAction] = Query(None),
    db: AsyncSession = Depends(get_tenant_session),
) -> StreamingResponse:
    """Export audit log as CSV download."""
    filters = AuditLogFilter(
        tenant_id=tenant_id,
        actor_id=actor_id,
        entity_type=entity_type,
        action=action,
    )
    svc = SuperAdminAuditService(db)
    csv_data = await svc.export_csv(filters)
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=audit_log.csv"
        },
    )
