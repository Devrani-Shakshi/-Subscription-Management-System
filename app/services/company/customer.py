"""
CustomerService — read-only customer listing + invite for company role.

Business rules:
- Company sees only portal_user customers in their tenant.
- Invite: 409 if pending invite exists, 409 if already registered.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import generate_invite_token, hash_token
from app.exceptions.base import ConflictException
from app.models.invite_token import InviteToken
from app.models.user import User
from app.schemas.company import CustomerInviteSchema, CustomerResponse


class CustomerService:
    """
    Customer management for company role.

    Unlike other services, customers are User records with
    role=portal_user, so this doesn't extend BaseEntityService.
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def list_all(
        self, *, offset: int = 0, limit: int = 100,
    ) -> Sequence[User]:
        """List all portal_user customers in this tenant."""
        query = (
            select(User)
            .where(
                User.tenant_id == self.tenant_id,
                User.role == UserRole.PORTAL_USER,
                User.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, customer_id: uuid.UUID) -> User:
        """Get a single customer by ID (scoped to tenant)."""
        query = select(User).where(
            User.id == customer_id,
            User.tenant_id == self.tenant_id,
            User.role == UserRole.PORTAL_USER,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()
        if customer is None:
            from app.exceptions.base import NotFoundException
            raise NotFoundException("Customer not found.")
        return customer

    async def count(self) -> int:
        """Count portal_user customers in tenant."""
        from sqlalchemy import func as sa_func

        query = (
            select(sa_func.count())
            .select_from(User)
            .where(
                User.tenant_id == self.tenant_id,
                User.role == UserRole.PORTAL_USER,
                User.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def invite(self, dto: CustomerInviteSchema) -> dict[str, Any]:
        """
        Generate portal_user invite.

        Raises:
            ConflictException: pending invite or already registered.
        """
        # Check for existing portal_user with this email in tenant
        existing_user = await self.db.execute(
            select(User).where(
                User.email == dto.email,
                User.tenant_id == self.tenant_id,
                User.role == UserRole.PORTAL_USER,
                User.deleted_at.is_(None),
            )
        )
        if existing_user.scalar_one_or_none():
            raise ConflictException(
                "Customer already has an account."
            )

        # Check for pending (unused, unexpired) invite
        now = datetime.utcnow()
        pending = await self.db.execute(
            select(InviteToken).where(
                InviteToken.email == dto.email,
                InviteToken.tenant_id == self.tenant_id,
                InviteToken.role == UserRole.PORTAL_USER,
                InviteToken.used_at.is_(None),
                InviteToken.expires_at > now,
                InviteToken.deleted_at.is_(None),
            )
        )
        if pending.scalar_one_or_none():
            raise ConflictException(
                "Invite already pending for this email."
            )

        # Create invite token
        raw_token = generate_invite_token()
        invite = InviteToken(
            tenant_id=self.tenant_id,
            email=dto.email,
            role=UserRole.PORTAL_USER,
            token_hash=hash_token(raw_token),
            expires_at=now + timedelta(hours=settings.INVITE_EXPIRE_HOURS),
        )
        self.db.add(invite)
        await self.db.flush()

        return {
            "invite_token": raw_token,
            "invite_url": f"{settings.FRONTEND_URL}/invite/{raw_token}",
        }
