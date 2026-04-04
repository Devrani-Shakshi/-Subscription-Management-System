"""
Auth router — public endpoints.

POST /auth/login
POST /auth/refresh
POST /auth/logout
POST /auth/seed
POST /auth/invite/accept
POST /auth/register
POST /auth/revoke-all

Every endpoint ≤ 10 lines. All logic in AuthService.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.dependencies.db import get_db_no_tenant
from app.dependencies.guards import get_current_user, get_tenant_session
from app.exceptions.base import AuthException, ForbiddenException
from app.schemas.auth import (
    InviteAcceptSchema,
    LoginResponse,
    LoginSchema,
    RegisterSchema,
    SeedSchema,
    TokenPayload,
)
from app.services.auth import AuthService
from app.services.portal import PortalService
from app.services.rate_limit import RateLimitService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_no_tenant),
) -> Response:
    """Authenticate → access_token + refresh cookie."""
    ip = _get_client_ip(request)
    await RateLimitService.check_login_email(body.email)
    await RateLimitService.check_login_ip(ip)

    svc = AuthService(db)
    result = await svc.login(body, ip)

    response = Response(
        content=LoginResponse(
            access_token=result["access_token"],
            role=result["role"],
            tenant_id=result["tenant_id"],
        ).model_dump_json(),
        media_type="application/json",
    )
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/auth/refresh",
    )
    return response


@router.post("/refresh")
async def refresh(
    request: Request,
    db: AsyncSession = Depends(get_db_no_tenant),
) -> Response:
    """Rotate refresh token → new access + refresh cookie."""
    old_refresh = request.cookies.get("refresh_token")
    if not old_refresh:
        raise AuthException("No refresh token.")

    await RateLimitService.check_refresh("unknown")

    svc = AuthService(db)
    result = await svc.refresh(old_refresh)

    response = Response(
        content=LoginResponse(
            access_token=result["access_token"],
            role=result["role"],
            tenant_id=result["tenant_id"],
        ).model_dump_json(),
        media_type="application/json",
    )
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/auth/refresh",
    )
    return response


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db_no_tenant),
) -> Response:
    """Revoke session. Always returns 204."""
    refresh_token = request.cookies.get("refresh_token")
    svc = AuthService(db)
    await svc.logout(refresh_token or "")

    response = Response(status_code=204)
    response.delete_cookie("refresh_token", path="/auth/refresh")
    return response


@router.post("/seed", status_code=201)
async def seed(
    body: SeedSchema,
    x_seed_secret: str = Header(..., alias="X-Seed-Secret"),
    db: AsyncSession = Depends(get_db_no_tenant),
) -> dict:
    """Bootstrap super_admin. Guarded by X-Seed-Secret header."""
    if x_seed_secret != settings.SEED_SECRET:
        raise ForbiddenException("Invalid seed secret.")

    svc = AuthService(db)
    user = await svc.seed_super_admin(body)
    return {"id": str(user.id), "email": user.email, "role": user.role.value}


@router.get("/invite/validate/{token}")
async def invite_validate(
    token: str,
    db: AsyncSession = Depends(get_db_no_tenant),
) -> dict:
    """Validate an invite token and return invite details."""
    from app.core.security import hash_token
    from app.models.invite_token import InviteToken
    from app.models.tenant import Tenant
    from sqlalchemy import select

    token_hash = hash_token(token)
    result = await db.execute(
        select(InviteToken).where(InviteToken.token_hash == token_hash)
    )
    invite = result.scalar_one_or_none()

    if invite is None:
        from app.exceptions.base import NotFoundException
        raise NotFoundException("Invalid invite link.")

    if invite.used_at is not None:
        from app.exceptions.base import AppException
        raise AppException("This invite has already been used.", status_code=410, code="INVITE_USED")

    from datetime import datetime
    now = datetime.utcnow()
    exp = invite.expires_at.replace(tzinfo=None) if invite.expires_at.tzinfo else invite.expires_at
    if exp < now:
        from app.exceptions.base import AppException
        raise AppException("Invite link expired.", status_code=410, code="INVITE_EXPIRED")

    # Get company name
    company_name = "Unknown"
    if invite.tenant_id:
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == invite.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if tenant:
            company_name = tenant.name

    return {
        "data": {
            "email": invite.email,
            "invitedBy": "Platform Admin",
            "role": invite.role.value,
            "companyName": company_name,
        }
    }


@router.post("/invite/accept", status_code=201)
async def invite_accept(
    body: InviteAcceptSchema,
    db: AsyncSession = Depends(get_db_no_tenant),
) -> dict:
    """Activate an invited account (company or portal_user)."""
    svc = AuthService(db)
    user = await svc.accept_invite(body)
    return {"id": str(user.id), "email": user.email, "role": user.role.value}


@router.post("/register", status_code=201)
async def register(
    body: RegisterSchema,
    request: Request,
    db: AsyncSession = Depends(get_db_no_tenant),
) -> Response:
    """Self-register as portal_user under a tenant. Auto-login on success."""
    ip = _get_client_ip(request)
    svc = AuthService(db)
    user = await svc.register_portal(body)

    # Auto-login: issue tokens immediately
    login_result = await svc.login_user_direct(user, ip)

    response = Response(
        content=LoginResponse(
            access_token=login_result["access_token"],
            role=login_result["role"],
            tenant_id=login_result["tenant_id"],
        ).model_dump_json(),
        media_type="application/json",
        status_code=201,
    )
    response.set_cookie(
        key="refresh_token",
        value=login_result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/auth/refresh",
    )
    return response


@router.post("/revoke-all")
async def revoke_all_devices(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Revoke all sessions for the current user across all devices."""
    svc = PortalService(db, user.user_id, user.tenant_id)
    return await svc.revoke_all_sessions()
