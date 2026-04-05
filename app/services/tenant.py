"""
Tenant service — company creation + invite generation.

Used by super_admin to create company accounts and
by company to invite portal_user customers.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import TenantStatus, UserRole
from app.core.security import generate_invite_token, hash_token
from app.exceptions.base import ConflictException, NotFoundException
from app.models.invite_token import InviteToken
from app.models.tenant import Tenant
from app.schemas.auth import CreateCompanySchema, InviteCustomerSchema
from app.services.base import BaseService


class TenantService(BaseService):
    """Create tenants and issue invite tokens."""

    async def create_company(self, dto: CreateCompanySchema) -> dict:
        """
        Create a tenant + generate a company invite token.

        Called by super_admin only.
        Returns tenant info + raw invite token for email delivery.
        """
        # Check slug uniqueness
        existing = await self.db.execute(
            select(Tenant).where(Tenant.slug == dto.slug)
        )
        if existing.scalar_one_or_none():
            raise ConflictException(f"Slug '{dto.slug}' is already taken.")

        # Create tenant
        tenant = Tenant(
            name=dto.name,
            slug=dto.slug,
            status=TenantStatus.TRIAL,
        )
        self.db.add(tenant)
        await self.db.flush()
        await self.db.refresh(tenant)

        # Generate invite token for company owner
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

        invite_url = f"{settings.FRONTEND_URL}/invite/{raw_token}"

        # Dispatch email
        from app.services.email import send_invite_email
        await send_invite_email(
            to=dto.email,
            company_name=tenant.name,
            invite_url=invite_url,
            role="company"
        )

        return {
            "tenant": tenant.to_dict(),
            "invite_token": raw_token,
            "invite_url": invite_url,
        }

    async def invite_customer(
        self,
        dto: InviteCustomerSchema,
        tenant_id: uuid.UUID,
    ) -> dict:
        """
        Generate a portal_user invite token.

        Called by company role for their own tenant.
        """
        raw_token = generate_invite_token()
        invite = InviteToken(
            tenant_id=tenant_id,
            email=dto.email,
            role=UserRole.PORTAL_USER,
            token_hash=hash_token(raw_token),
            expires_at=datetime.utcnow()
            + timedelta(hours=settings.INVITE_EXPIRE_HOURS),
        )
        self.db.add(invite)
        await self.db.flush()

        invite_url = f"{settings.FRONTEND_URL}/invite/{raw_token}"

        # Fetch tenant to get company name for the email
        res = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = res.scalar_one()

        # Dispatch email (fire and forget or await)
        from app.services.email import send_invite_email
        await send_invite_email(
            to=dto.email,
            company_name=tenant.name,
            invite_url=invite_url,
            role="portal_user"
        )

        return {
            "invite_token": raw_token,
            "invite_url": invite_url,
        }

    async def get_tenant_by_slug(self, slug: str) -> Tenant:
        """Public endpoint: get tenant branding info by slug."""
        result = await self.db.execute(
            select(Tenant).where(
                Tenant.slug == slug, Tenant.deleted_at.is_(None)
            )
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundException("Tenant not found.")
        return tenant
