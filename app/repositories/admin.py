"""
Super-admin repository — cross-tenant data access for admin operations.

Extends SuperAdminRepository with typed concrete repositories for
Tenant, User, Subscription, Invoice, AuditLog, and Payment models.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional, Sequence, Type

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.base import SuperAdminRepository


class TenantRepository(SuperAdminRepository[Tenant]):
    """Cross-tenant access to the tenants table."""

    model = Tenant

    async def find_by_slug(self, slug: str) -> Tenant | None:
        """Lookup tenant by slug (soft-delete aware)."""
        query = self._base_query().where(Tenant.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        """Check if a slug is already taken."""
        query = (
            select(func.count())
            .select_from(Tenant)
            .where(and_(Tenant.slug == slug, Tenant.deleted_at.is_(None)))
        )
        result = await self.db.execute(query)
        return result.scalar_one() > 0

    async def list_with_stats(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[Sequence[Tenant], int]:
        """List tenants with optional filters, return (items, total)."""
        base = self._base_query()
        count_base = self._scope(
            select(func.count()).select_from(Tenant)
        )

        if status_filter:
            base = base.where(Tenant.status == status_filter)
            count_base = count_base.where(Tenant.status == status_filter)
        if search:
            pattern = f"%{search}%"
            base = base.where(Tenant.name.ilike(pattern))
            count_base = count_base.where(Tenant.name.ilike(pattern))

        count_result = await self.db.execute(count_base)
        total = count_result.scalar_one()

        query = base.order_by(Tenant.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total


class UserRepository(SuperAdminRepository[User]):
    """Cross-tenant access to the users table."""

    model = User

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email."""
        query = self._base_query().where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_by_tenant(
        self, tenant_id: uuid.UUID, role: Optional[str] = None
    ) -> int:
        """Count users belonging to a tenant."""
        filters = [User.tenant_id == tenant_id, User.deleted_at.is_(None)]
        if role:
            filters.append(User.role == role)
        query = select(func.count()).select_from(User).where(and_(*filters))
        result = await self.db.execute(query)
        return result.scalar_one()

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, *, offset: int = 0, limit: int = 100
    ) -> Sequence[User]:
        """List users in a tenant."""
        query = (
            self._base_query()
            .where(User.tenant_id == tenant_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class SubscriptionRepository(SuperAdminRepository[Subscription]):
    """Cross-tenant access to subscriptions."""

    model = Subscription

    async def count_active_by_tenant(self, tenant_id: uuid.UUID) -> int:
        """Count active subscriptions for a tenant."""
        query = (
            select(func.count())
            .select_from(Subscription)
            .where(
                and_(
                    Subscription.tenant_id == tenant_id,
                    Subscription.status.in_(["confirmed", "active"]),
                    Subscription.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def count_active_total(self) -> int:
        """Count all active subscriptions across all tenants."""
        query = (
            select(func.count())
            .select_from(Subscription)
            .where(
                and_(
                    Subscription.status.in_(["confirmed", "active"]),
                    Subscription.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, *, offset: int = 0, limit: int = 100
    ) -> Sequence[Subscription]:
        """List subscriptions for a tenant."""
        query = (
            self._base_query()
            .where(Subscription.tenant_id == tenant_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class InvoiceRepository(SuperAdminRepository[Invoice]):
    """Cross-tenant access to invoices."""

    model = Invoice

    async def count_by_tenant(self, tenant_id: uuid.UUID) -> int:
        """Count invoices for a tenant."""
        query = (
            select(func.count())
            .select_from(Invoice)
            .where(
                and_(
                    Invoice.tenant_id == tenant_id,
                    Invoice.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, *, offset: int = 0, limit: int = 100
    ) -> Sequence[Invoice]:
        """List invoices for a tenant."""
        query = (
            self._base_query()
            .where(Invoice.tenant_id == tenant_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class PaymentRepository(SuperAdminRepository[Payment]):
    """Cross-tenant access to payments."""

    model = Payment

    async def sum_by_tenant(self, tenant_id: uuid.UUID) -> float:
        """Sum all payments for a tenant (MRR proxy)."""
        query = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .select_from(Payment)
            .where(
                and_(
                    Payment.tenant_id == tenant_id,
                    Payment.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(query)
        return float(result.scalar_one())

    async def sum_total(self) -> float:
        """Sum all payments across all tenants."""
        query = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .select_from(Payment)
            .where(Payment.deleted_at.is_(None))
        )
        result = await self.db.execute(query)
        return float(result.scalar_one())


class AuditLogRepository(SuperAdminRepository[AuditLog]):
    """Cross-tenant access to audit_log."""

    model = AuditLog

    async def list_filtered(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        date_from: Any = None,
        date_to: Any = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[AuditLog], int]:
        """List audit logs with filters, return (items, total)."""
        base = select(AuditLog).where(AuditLog.deleted_at.is_(None))
        count_q = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.deleted_at.is_(None))
        )

        conditions: list[Any] = []
        if tenant_id:
            conditions.append(AuditLog.tenant_id == tenant_id)
        if actor_id:
            conditions.append(AuditLog.actor_id == actor_id)
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if action:
            conditions.append(AuditLog.action == action)
        if date_from:
            conditions.append(AuditLog.created_at >= date_from)
        if date_to:
            conditions.append(AuditLog.created_at <= date_to)

        if conditions:
            base = base.where(and_(*conditions))
            count_q = count_q.where(and_(*conditions))

        count_result = await self.db.execute(count_q)
        total = count_result.scalar_one()

        query = base.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def find_by_tenant(
        self, tenant_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> Sequence[AuditLog]:
        """List audit log entries for a specific tenant."""
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.tenant_id == tenant_id,
                    AuditLog.deleted_at.is_(None),
                )
            )
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
