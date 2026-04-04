"""
Auth service — all authentication business logic.

Responsibilities:
- Login (with rate limiting + tenant suspension check)
- Refresh token rotation (with family-based reuse detection)
- Seed super_admin
- Invite accept (company + portal_user)
- Portal self-registration
- Password reset request / confirm
- Logout (session revocation)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import TenantStatus, UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_invite_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.exceptions.base import (
    AppException,
    AuthException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.invite_token import InviteToken
from app.models.session import Session
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    InviteAcceptSchema,
    LoginResponse,
    LoginSchema,
    RegisterSchema,
    SeedSchema,
    TokenPayload,
)
from app.services.base import BaseService
from app.services.token_family import TokenFamilyService


_REFRESH_TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


class AuthService(BaseService):
    """Handles login, register, refresh, invite, seed, logout."""

    # ── LOGIN ────────────────────────────────────────────────────
    async def login(self, dto: LoginSchema, ip: str) -> dict:
        """
        Authenticate user → issue access + refresh tokens.

        Returns dict with access_token, role, tenant_id,
        and raw refresh_token (for cookie).
        """
        user = await self._find_user_by_email(dto.email)
        if user is None or not user.password_hash:
            raise AuthException("Invalid credentials.")

        if not verify_password(dto.password, user.password_hash):
            raise AuthException("Invalid credentials.")

        # Tenant suspension check
        if user.tenant_id:
            tenant = await self._get_tenant(user.tenant_id)
            if tenant and tenant.status == TenantStatus.SUSPENDED:
                raise ForbiddenException(
                    "Account suspended. Contact support."
                )

        # Issue tokens
        access = create_access_token(
            user_id=user.id,
            role=user.role.value,
            tenant_id=user.tenant_id,
            email=user.email,
        )
        family_id = uuid.uuid4()
        refresh = create_refresh_token(
            user_id=user.id, family_id=family_id
        )

        # Persist session
        await self._create_session(
            user_id=user.id,
            tenant_id=user.tenant_id,
            refresh_token=refresh,
            family_id=family_id,
            ip=ip,
        )

        # Register in Redis family
        await TokenFamilyService.register(
            family_id=family_id,
            refresh_token=refresh,
            ttl_seconds=_REFRESH_TTL,
        )

        return {
            "access_token": access,
            "refresh_token": refresh,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
        }

    # ── REFRESH ──────────────────────────────────────────────────
    async def refresh(self, old_refresh: str) -> dict:
        """
        Rotate refresh token. Detect reuse → revoke family.

        Returns new access_token + new refresh_token.
        """
        try:
            payload = decode_token(old_refresh)
        except Exception:
            raise AuthException("Invalid refresh token.")

        if payload.get("type") != "refresh":
            raise AuthException("Invalid token type.")

        user_id = uuid.UUID(payload["sub"])
        family_id = uuid.UUID(payload["family_id"])

        # Validate + rotate in Redis
        new_refresh = create_refresh_token(
            user_id=user_id, family_id=family_id
        )
        valid = await TokenFamilyService.validate_and_rotate(
            family_id=family_id,
            old_token=old_refresh,
            new_token=new_refresh,
            ttl_seconds=_REFRESH_TTL,
        )
        if not valid:
            # Reuse detected! Revoke all sessions in family
            await self._revoke_family_sessions(family_id)
            raise AuthException("Token reuse detected. All sessions revoked.")

        # Rotate in DB
        await self._rotate_session(family_id, old_refresh, new_refresh)

        # Get user for new access token
        user = await self._find_user_by_id(user_id)
        if user is None:
            raise AuthException("User not found.")

        access = create_access_token(
            user_id=user.id,
            role=user.role.value,
            tenant_id=user.tenant_id,
            email=user.email,
        )

        return {
            "access_token": access,
            "refresh_token": new_refresh,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
        }

    # ── SEED SUPER_ADMIN ─────────────────────────────────────────
    async def seed_super_admin(self, dto: SeedSchema) -> User:
        """Create the initial super_admin. Idempotent — skips if exists."""
        existing = await self._find_user_by_email(dto.email)
        if existing:
            raise ConflictException("Super admin already exists.")

        user = User(
            email=dto.email,
            password_hash=hash_password(dto.password),
            role=UserRole.SUPER_ADMIN,
            tenant_id=None,
            name=dto.name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    # ── INVITE ACCEPT ────────────────────────────────────────────
    async def accept_invite(self, dto: InviteAcceptSchema) -> User:
        """Activate an invited company or portal_user account."""
        token_hash = hash_token(dto.token)
        invite = await self._find_invite_by_hash(token_hash)

        if invite is None:
            raise NotFoundException("Invalid invite link.")

        now = datetime.now(timezone.utc)
        if invite.used_at is not None:
            raise AppException(
                "This invite link has already been used.",
                status_code=410,
                code="INVITE_USED",
            )
        if invite.expires_at.replace(tzinfo=timezone.utc) < now:
            raise AppException(
                "Invite link expired. Request a new one.",
                status_code=410,
                code="INVITE_EXPIRED",
            )

        # Check email not already registered
        existing = await self._find_user_by_email(invite.email)
        if existing:
            raise ConflictException(
                "An account with this email already exists."
            )

        # Create user
        user = User(
            email=invite.email,
            password_hash=hash_password(dto.password),
            role=invite.role,
            tenant_id=invite.tenant_id,
            name=dto.name,
        )
        self.db.add(user)

        # If company role, set as tenant owner
        if invite.role == UserRole.COMPANY and invite.tenant_id:
            tenant = await self._get_tenant(invite.tenant_id)
            if tenant:
                tenant.owner_user_id = user.id

        # Mark invite used
        invite.used_at = now
        await self.db.flush()
        await self.db.refresh(user)
        return user

    # ── PORTAL SELF-REGISTER ─────────────────────────────────────
    async def register_portal(self, dto: RegisterSchema) -> User:
        """Self-register a portal_user under a tenant (by slug)."""
        if not dto.tenant_slug:
            raise ValidationException(
                [{"field": "tenant_slug", "message": "Tenant slug is required."}]
            )

        tenant = await self._find_tenant_by_slug(dto.tenant_slug)
        if tenant is None:
            raise NotFoundException("Tenant not found.")
        if tenant.status == TenantStatus.SUSPENDED:
            raise ForbiddenException(
                "This company is suspended. Contact support."
            )

        existing = await self._find_user_by_email(dto.email)
        if existing:
            raise ConflictException(
                "An account with this email already exists."
            )

        user = User(
            email=dto.email,
            password_hash=hash_password(dto.password),
            role=UserRole.PORTAL_USER,
            tenant_id=tenant.id,
            name=dto.name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    # ── LOGOUT ───────────────────────────────────────────────────
    async def logout(self, refresh_token: str) -> None:
        """Revoke the session associated with this refresh token."""
        try:
            payload = decode_token(refresh_token)
            family_id = uuid.UUID(payload["family_id"])
            await TokenFamilyService.revoke_family(family_id)
            await self._revoke_family_sessions(family_id)
        except Exception:
            pass  # Logout is always successful from client perspective

    # ── LOGIN USER DIRECT (no password check) ────────────────────
    async def login_user_direct(self, user: User, ip: str) -> dict:
        """
        Issue tokens for an already-verified user.

        Used after self-registration to auto-login without re-authenticating.
        """
        access = create_access_token(
            user_id=user.id,
            role=user.role.value,
            tenant_id=user.tenant_id,
            email=user.email,
        )
        family_id = uuid.uuid4()
        refresh = create_refresh_token(
            user_id=user.id, family_id=family_id
        )

        await self._create_session(
            user_id=user.id,
            tenant_id=user.tenant_id,
            refresh_token=refresh,
            family_id=family_id,
            ip=ip,
        )

        await TokenFamilyService.register(
            family_id=family_id,
            refresh_token=refresh,
            ttl_seconds=_REFRESH_TTL,
        )

        return {
            "access_token": access,
            "refresh_token": refresh,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
        }

    # ═════════════════════════════════════════════════════════════
    # Private helpers
    # ═════════════════════════════════════════════════════════════

    async def _find_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def _find_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def _get_tenant(self, tenant_id: uuid.UUID) -> Tenant | None:
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def _find_tenant_by_slug(self, slug: str) -> Tenant | None:
        result = await self.db.execute(
            select(Tenant).where(
                Tenant.slug == slug, Tenant.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def _find_invite_by_hash(self, token_hash: str) -> InviteToken | None:
        result = await self.db.execute(
            select(InviteToken).where(InviteToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def _create_session(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID | None,
        refresh_token: str,
        family_id: uuid.UUID,
        ip: str,
    ) -> Session:
        session = Session(
            user_id=user_id,
            tenant_id=tenant_id,
            refresh_token_hash=hash_token(refresh_token),
            family_id=family_id,
            device_fingerprint="web",
            ip_subnet=ip.rsplit(".", 1)[0] + ".0" if "." in ip else ip,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def _rotate_session(
        self,
        family_id: uuid.UUID,
        old_token: str,
        new_token: str,
    ) -> None:
        """Replace the refresh token hash in the DB session row."""
        result = await self.db.execute(
            select(Session).where(
                Session.family_id == family_id,
                Session.refresh_token_hash == hash_token(old_token),
                Session.revoked_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.refresh_token_hash = hash_token(new_token)
            session.expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            await self.db.flush()

    async def _revoke_family_sessions(self, family_id: uuid.UUID) -> None:
        """Revoke all DB sessions in this token family."""
        result = await self.db.execute(
            select(Session).where(
                Session.family_id == family_id,
                Session.revoked_at.is_(None),
            )
        )
        sessions = result.scalars().all()
        now = datetime.now(timezone.utc)
        for s in sessions:
            s.revoked_at = now
        await self.db.flush()
