"""
Portal router — portal_user only.

Self-service endpoints for subscription, invoices, plan changes.

Routes:
  GET   /portal/me
  GET   /portal/my-subscription
  GET   /portal/my-subscription/change-plan/preview
  POST  /portal/my-subscription/change-plan
  POST  /portal/my-subscription/cancel
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.guards import get_tenant_session, require_portal_user
from app.schemas.auth import TokenPayload
from app.schemas.subscription import CancelRequest, ChangePlanRequest
from app.services.subscriptions.portal import PortalSubscriptionService

router = APIRouter(
    prefix="/portal",
    tags=["portal"],
    dependencies=[Depends(require_portal_user)],
)


# ── Service factory ─────────────────────────────────────────────

def _portal_sub_svc(
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> PortalSubscriptionService:
    return PortalSubscriptionService(db, user.tenant_id, user.user_id)


# ═══════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════

@router.get("/me")
async def get_me(
    user: TokenPayload = Depends(require_portal_user),
) -> dict:
    """Return authenticated portal_user profile."""
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
    }


# ═══════════════════════════════════════════════════════════════
# Subscription self-service
# ═══════════════════════════════════════════════════════════════

@router.get("/my-subscription")
async def get_my_subscription(
    svc: PortalSubscriptionService = Depends(_portal_sub_svc),
) -> dict:
    """Portal: full subscription details with plan, lines, invoices."""
    return await svc.get_my_subscription()


@router.get("/my-subscription/change-plan/preview")
async def change_plan_preview(
    plan_id: UUID = Query(...),
    svc: PortalSubscriptionService = Depends(_portal_sub_svc),
) -> dict:
    """Preview pro-rata amounts for a plan switch."""
    return await svc.change_plan_preview(plan_id)


@router.post("/my-subscription/change-plan")
async def change_plan(
    body: ChangePlanRequest,
    svc: PortalSubscriptionService = Depends(_portal_sub_svc),
) -> dict:
    """Execute a plan change (upgrade=immediate, downgrade=scheduled)."""
    return await svc.change_plan(body.plan_id)


@router.post("/my-subscription/cancel")
async def cancel_subscription(
    body: CancelRequest = CancelRequest(),
    svc: PortalSubscriptionService = Depends(_portal_sub_svc),
) -> dict:
    """Cancel the portal user's subscription."""
    return await svc.cancel(reason=body.reason)
