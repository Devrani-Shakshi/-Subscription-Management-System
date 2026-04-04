"""
Portal router — portal_user only.

Placeholder for subscription/invoice/payment self-service endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.guards import require_portal_user
from app.schemas.auth import TokenPayload

router = APIRouter(
    prefix="/portal",
    tags=["portal"],
    dependencies=[Depends(require_portal_user)],
)


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
