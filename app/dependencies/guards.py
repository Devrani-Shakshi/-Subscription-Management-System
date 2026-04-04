"""
Role + Ownership guards — FastAPI Depends() callables.

RoleGuard: require_super_admin, require_company, require_portal_user
OwnershipGuard: require_owner (portal routes only)
get_current_user: extract TokenPayload from request.state
get_tenant_session: yield DB session with RLS tenant_id set
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db, get_db_no_tenant
from app.exceptions.base import AuthException, ForbiddenException
from app.schemas.auth import TokenPayload


# ── Current user ─────────────────────────────────────────────────
security = HTTPBearer()


def get_current_user(
    request: Request,
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """Extract authenticated user from request.state (set by JWTMiddleware)."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise AuthException("Authentication required.")
    return user


# ── Role guards ──────────────────────────────────────────────────
def require_super_admin(
    user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    if user.role != "super_admin":
        raise ForbiddenException("Access denied.")
    return user


def require_company(
    user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    if user.role != "company":
        raise ForbiddenException("Access denied.")
    return user


def require_portal_user(
    user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    if user.role != "portal_user":
        raise ForbiddenException("Access denied.")
    return user


# ── Tenant-scoped DB session ────────────────────────────────────
async def get_tenant_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a DB session with RLS tenant_id set from request.state.tenant.

    For super_admin requests, tenant_id is None → RLS set to 'SUPER'.
    """
    tenant_id = getattr(request.state, "tenant", None)
    async for session in get_db(tenant_id):
        yield session


# ── Ownership guard for portal routes ────────────────────────────
class OwnershipGuard:
    """
    Ensure the authenticated portal_user owns the requested resource.

    Usage in router:
        @router.get("/{sub_id}")
        async def get_sub(
            sub_id: UUID,
            user: TokenPayload = Depends(require_portal_user),
            db: AsyncSession = Depends(get_tenant_session),
            _: None = Depends(OwnershipGuard("customer_id")),
        ):
    """

    def __init__(self, owner_field: str = "customer_id") -> None:
        self.owner_field = owner_field

    async def __call__(
        self,
        request: Request,
        user: TokenPayload = Depends(get_current_user),
    ) -> None:
        """
        Called as Depends(). Validates ownership at the service layer,
        not here. This guard only sets context for downstream checks.
        """
        if user.role != "portal_user":
            return
        # Store the ownership field on request for the service to check
        request.state.owner_field = self.owner_field
        request.state.owner_id = user.user_id
