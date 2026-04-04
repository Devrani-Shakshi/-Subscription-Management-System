"""
Company router — company role only.

POST /company/customers/invite  — invite portal_user
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.guards import get_tenant_session, require_company
from app.schemas.auth import InviteCustomerSchema, TokenPayload
from app.services.tenant import TenantService

router = APIRouter(
    prefix="/company",
    tags=["company"],
    dependencies=[Depends(require_company)],
)


@router.post("/customers/invite", status_code=201)
async def invite_customer(
    body: InviteCustomerSchema,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Invite a portal_user customer."""
    svc = TenantService(db)
    return await svc.invite_customer(body, tenant_id=user.tenant_id)
