"""
Public router — no auth required.

GET /public/tenant/{slug}  — get tenant branding info
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db_no_tenant
from app.schemas.auth import TenantPublicSchema
from app.services.tenant import TenantService

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/tenant/{slug}", response_model=TenantPublicSchema)
async def get_tenant_branding(
    slug: str,
    db: AsyncSession = Depends(get_db_no_tenant),
) -> TenantPublicSchema:
    """Public: tenant branding for login screen."""
    svc = TenantService(db)
    tenant = await svc.get_tenant_by_slug(slug)
    return TenantPublicSchema(
        name=tenant.name,
        slug=tenant.slug,
        logo_url=None,
        primary_color=None,
    )
