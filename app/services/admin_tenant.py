"""
Super-admin tenant service — company CRUD + lifecycle management.

Handles:
- Create company (tenant + user + invite)
- Suspend / reactivate tenants
- Soft-delete tenants (guarded by active subscriptions)
- Slug uniqueness checks
- Tenant detail retrieval

All operations use SuperAdminRepository (no tenant filter).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import AuditAction, TenantStatus, UserRole
from app.core.security import generate_invite_token, hash_token
from app.exceptions.base import ConflictException, NotFoundException
from app.models.invite_token import InviteToken
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.admin import (
    InvoiceRepository,
    SubscriptionRepository,
    TenantRepository,
    UserRepository,
)
from app.schemas.admin import (
    CompanyCreateResponse,
    CreateCompanySchema,
    DeleteCompanyResponse,
    SlugCheckResponse,
    SuspendReactivateResponse,
    TenantDetailResponse,
    TenantListItem,
    TenantListResponse,
)
from app.services.audit_logger import AuditLogger
from app.services.base import BaseService

logger = logging.getLogger(__name__)


class SuperAdminTenantService(BaseService):
    """Business logic for super_admin company management."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._tenants = TenantRepository(db)
        self._users = UserRepository(db)
        self._subs = SubscriptionRepository(db)
        self._invoices = InvoiceRepository(db)
        self._audit = AuditLogger(db)

    # ── CREATE ───────────────────────────────────────────────────
    async def create_company(
        self, dto: CreateCompanySchema, actor_id: uuid.UUID
    ) -> CompanyCreateResponse:
        """
        Create tenant + placeholder company user + invite token.

        Steps:
        1. Validate slug uniqueness
        2. Create Tenant row (status=trial)
        3. Create User row (password_hash=None, role=company)
        4. Create InviteToken (role=company, 48h expiry)
        5. Log audit entry
        """
        if await self._tenants.slug_exists(dto.slug):
            raise ConflictException(
                f"URL '{dto.slug}' is taken. Try '{dto.slug}-co'."
            )

        # 1. Create tenant
        tenant = Tenant(
            name=dto.name,
            slug=dto.slug,
            status=TenantStatus.TRIAL,
            trial_ends_at=datetime.utcnow() + timedelta(days=14),
        )
        self.db.add(tenant)
        await self.db.flush()
        await self.db.refresh(tenant)

        # 2. Create company user (no password yet — invite flow)
        user = User(
            email=dto.email,
            password_hash=None,
            role=UserRole.COMPANY,
            tenant_id=tenant.id,
            name=dto.name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        # Set owner
        tenant.owner_user_id = user.id
        await self.db.flush()

        # 3. Generate invite token
        raw_token = generate_invite_token()
        invite = InviteToken(
            tenant_id=tenant.id,
            email=dto.email,
            role=UserRole.COMPANY,
            token_hash=hash_token(raw_token),
            expires_at=datetime.utcnow()
            + timedelta(hours=settings.INVITE_EXPIRE_HOURS),
        )
        self.db.add(invite)
        await self.db.flush()

        # 4. Audit
        await self._audit.log(
            actor_id=actor_id,
            actor_role=UserRole.SUPER_ADMIN,
            tenant_id=None,
            entity_type="tenant",
            entity_id=tenant.id,
            action=AuditAction.CREATE,
            after={"name": dto.name, "slug": dto.slug, "email": dto.email},
        )

        # 5. Send invite email (best-effort, don't fail the request)
        invite_url = f"{settings.FRONTEND_URL}/invite/{raw_token}"
        try:
            from app.services.email import send_invite_email
            await send_invite_email(
                to=dto.email,
                company_name=dto.name,
                invite_url=invite_url,
                role="company",
            )
        except Exception:
            logger.warning("Failed to send invite email to %s", dto.email)

        return CompanyCreateResponse(
            tenant_id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            invite_url=invite_url,
            invite_token=raw_token,
        )

    # ── LIST ─────────────────────────────────────────────────────
    async def list_companies(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        search: str | None = None,
    ) -> TenantListResponse:
        """List all tenants with MRR and subscription counts."""
        offset = (page - 1) * page_size
        tenants, total = await self._tenants.list_with_stats(
            offset=offset,
            limit=page_size,
            status_filter=status,
            search=search,
        )

        items: list[TenantListItem] = []
        for t in tenants:
            active_count = await self._subs.count_active_by_tenant(t.id)
            items.append(
                TenantListItem(
                    id=t.id,
                    name=t.name,
                    slug=t.slug,
                    status=t.status,
                    mrr=Decimal("0.00"),
                    active_subs_count=active_count,
                    trial_ends_at=t.trial_ends_at,
                    created_at=t.created_at,
                )
            )

        return TenantListResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    # ── DETAIL ───────────────────────────────────────────────────
    async def get_company_detail(
        self, tenant_id: uuid.UUID
    ) -> TenantDetailResponse:
        """Get full tenant detail with aggregated tab data."""
        tenant = await self._tenants.find_by_id(tenant_id)

        active_subs = await self._subs.count_active_by_tenant(tenant_id)
        total_customers = await self._users.count_by_tenant(
            tenant_id, role="portal_user"
        )
        total_invoices = await self._invoices.count_by_tenant(tenant_id)

        owner_email: str | None = None
        owner_name: str | None = None
        if tenant.owner:
            owner_email = tenant.owner.email
            owner_name = tenant.owner.name

        return TenantDetailResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            status=tenant.status,
            owner_email=owner_email,
            owner_name=owner_name,
            mrr=Decimal("0.00"),
            active_subs_count=active_subs,
            total_customers=total_customers,
            total_invoices=total_invoices,
            trial_ends_at=tenant.trial_ends_at,
            created_at=tenant.created_at,
        )

    # ── SUSPEND ──────────────────────────────────────────────────
    async def suspend_company(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID
    ) -> SuspendReactivateResponse:
        """
        Suspend a tenant — blocks all user logins.

        Guards:
        - Cannot suspend an already-suspended tenant.
        """
        tenant = await self._tenants.find_by_id(tenant_id)

        if tenant.status == TenantStatus.SUSPENDED:
            raise ConflictException("Company is already suspended.")

        before_status = tenant.status.value
        tenant.status = TenantStatus.SUSPENDED
        await self.db.flush()

        await self._audit.log(
            actor_id=actor_id,
            actor_role=UserRole.SUPER_ADMIN,
            tenant_id=None,
            entity_type="tenant",
            entity_id=tenant.id,
            action=AuditAction.STATUS_CHANGE,
            before={"status": before_status},
            after={"status": TenantStatus.SUSPENDED.value},
        )

        return SuspendReactivateResponse(
            tenant_id=tenant.id,
            status=TenantStatus.SUSPENDED,
            message=f"Company '{tenant.name}' has been suspended.",
        )

    # ── REACTIVATE ───────────────────────────────────────────────
    async def reactivate_company(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID
    ) -> SuspendReactivateResponse:
        """
        Reactivate a suspended tenant.

        Guards:
        - Cannot reactivate an already-active tenant.
        """
        tenant = await self._tenants.find_by_id(tenant_id)

        if tenant.status != TenantStatus.SUSPENDED:
            raise ConflictException("Company is already active.")

        tenant.status = TenantStatus.ACTIVE
        await self.db.flush()

        await self._audit.log(
            actor_id=actor_id,
            actor_role=UserRole.SUPER_ADMIN,
            tenant_id=None,
            entity_type="tenant",
            entity_id=tenant.id,
            action=AuditAction.STATUS_CHANGE,
            before={"status": TenantStatus.SUSPENDED.value},
            after={"status": TenantStatus.ACTIVE.value},
        )

        return SuspendReactivateResponse(
            tenant_id=tenant.id,
            status=TenantStatus.ACTIVE,
            message=f"Company '{tenant.name}' has been reactivated.",
        )

    # ── DELETE ───────────────────────────────────────────────────
    async def delete_company(
        self, tenant_id: uuid.UUID, actor_id: uuid.UUID
    ) -> DeleteCompanyResponse:
        """
        Soft-delete a tenant and all its resources.

        Guards:
        - Cannot delete if active subscriptions exist.
        """
        tenant = await self._tenants.find_by_id(tenant_id)
        active_subs = await self._subs.count_active_by_tenant(tenant_id)

        if active_subs > 0:
            raise ConflictException(
                f"Cannot delete — {active_subs} active subscription(s) exist."
            )

        # Soft-delete tenant
        tenant.soft_delete()
        await self.db.flush()

        await self._audit.log(
            actor_id=actor_id,
            actor_role=UserRole.SUPER_ADMIN,
            tenant_id=None,
            entity_type="tenant",
            entity_id=tenant.id,
            action=AuditAction.DELETE,
            before={"name": tenant.name, "status": tenant.status.value},
        )

        return DeleteCompanyResponse(
            tenant_id=tenant.id,
            message=f"Company '{tenant.name}' has been deleted.",
        )

    # ── SLUG CHECK ───────────────────────────────────────────────
    async def check_slug(self, slug: str) -> SlugCheckResponse:
        """Check if a slug is available, suggest alternative if not."""
        exists = await self._tenants.slug_exists(slug)
        if exists:
            suggestion = f"{slug}-co"
            while await self._tenants.slug_exists(suggestion):
                suggestion = f"{slug}-{uuid.uuid4().hex[:4]}"
            return SlugCheckResponse(available=False, suggestion=suggestion)
        return SlugCheckResponse(available=True)
