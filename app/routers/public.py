"""
Public router — no auth required.

GET /public/tenant/{slug}     — get tenant branding info
GET /public/plans?tenant=slug — get plans for a tenant (public pricing page)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db_no_tenant
from app.exceptions.base import ForbiddenException, NotFoundException
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.core.enums import TenantStatus
from app.schemas.auth import TenantPublicSchema
from app.schemas.company import PlanPreviewResponse
from app.services.tenant import TenantService

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/tenant/{slug}", response_model=TenantPublicSchema)
async def get_tenant_branding(
    slug: str,
    db: AsyncSession = Depends(get_db_no_tenant),
) -> TenantPublicSchema:
    """Public: tenant branding for login/register screen."""
    svc = TenantService(db)
    tenant = await svc.get_tenant_by_slug(slug)

    # Check suspension — return friendly message
    if tenant.status == TenantStatus.SUSPENDED:
        raise ForbiddenException(
            f"{tenant.name}'s services are temporarily unavailable. "
            f"Please contact {tenant.name} for assistance."
        )

    return TenantPublicSchema(
        name=tenant.name,
        slug=tenant.slug,
        logo_url=getattr(tenant, "logo_url", None),
        primary_color=getattr(tenant, "primary_color", None),
    )


@router.get("/plans")
async def list_public_plans(
    tenant: str = Query(..., description="Tenant slug"),
    db: AsyncSession = Depends(get_db_no_tenant),
) -> list[dict]:
    """Public pricing page: list all active plans for a tenant."""
    # Resolve slug → tenant_id
    result = await db.execute(
        select(Tenant).where(
            Tenant.slug == tenant,
            Tenant.deleted_at.is_(None),
        )
    )
    tenant_obj = result.scalar_one_or_none()
    if tenant_obj is None:
        raise NotFoundException("Tenant not found.")

    # Check suspension
    if tenant_obj.status == TenantStatus.SUSPENDED:
        raise ForbiddenException(
            f"{tenant_obj.name}'s services are temporarily unavailable. "
            f"Please contact {tenant_obj.name} for assistance."
        )

    # Fetch active plans
    plans_result = await db.execute(
        select(Plan).where(
            Plan.tenant_id == tenant_obj.id,
            Plan.deleted_at.is_(None),
        )
    )
    plans = plans_result.scalars().all()

    return [
        PlanPreviewResponse(
            id=p.id,
            name=p.name,
            price=p.price,
            billing_period=p.billing_period,
            features=p.features_json,
            flags=p.flags_json,
        ).model_dump()
        for p in plans
    ]
