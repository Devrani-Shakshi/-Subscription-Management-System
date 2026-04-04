"""
Admin router — super_admin only.

POST /admin/companies  — create company tenant + invite
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.guards import get_tenant_session, require_super_admin
from app.schemas.auth import CreateCompanySchema, TokenPayload
from app.services.tenant import TenantService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_super_admin)],
)


@router.post("/companies", status_code=201)
async def create_company(
    body: CreateCompanySchema,
    user: TokenPayload = Depends(require_super_admin),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Create a new company tenant and generate invite."""
    svc = TenantService(db)
    return await svc.create_company(body)
