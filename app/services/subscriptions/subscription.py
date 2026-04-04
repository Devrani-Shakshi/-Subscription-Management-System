"""
SubscriptionService — company-side subscription management.

Responsibilities:
- Create subscriptions (multi-step wizard, status=draft)
- List / get subscriptions with tenant scoping
- Activate (draft → quotation → confirmed → active)
- Close subscriptions
- Bulk operations
- Auto-generate subscription numbers
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import SubscriptionStatus
from app.exceptions.base import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.subscription_line import SubscriptionLine
from app.models.user import User
from app.repositories.base import BaseRepository
from app.services.subscriptions.event_bus import event_bus
from app.services.subscriptions.fsm import SubscriptionStatusFSM
from app.services.subscriptions.invoice_factory import InvoiceFactory


class SubscriptionService:
    """
    Company-scoped subscription management.

    All operations are tenant-isolated via BaseRepository.
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.repo = self._make_repo()

    def _make_repo(self) -> BaseRepository[Subscription]:
        repo: BaseRepository[Subscription] = BaseRepository(
            self.db, self.tenant_id
        )
        repo.model = Subscription
        return repo

    # ── LIST ─────────────────────────────────────────────────────

    async def list_all(
        self,
        *,
        status: SubscriptionStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Subscription]:
        """List subscriptions with optional status filter."""
        filters: list[Any] = []
        if status is not None:
            filters.append(Subscription.status == status)
        return await self.repo.find_all(
            filters=filters, offset=offset, limit=limit
        )

    async def count(
        self,
        *,
        status: SubscriptionStatus | None = None,
    ) -> int:
        """Count subscriptions with optional status filter."""
        filters: list[Any] = []
        if status is not None:
            filters.append(Subscription.status == status)
        return await self.repo.count(*filters)

    # ── GET ──────────────────────────────────────────────────────

    async def get_by_id(self, sub_id: uuid.UUID) -> Subscription:
        """Get subscription by ID with lines eagerly loaded."""
        return await self.repo.find_by_id(sub_id)

    # ── CREATE (wizard step 5 → POST) ───────────────────────────

    async def create(
        self,
        customer_id: uuid.UUID,
        plan_id: uuid.UUID,
        start_date: date,
        expiry_date: date,
        payment_terms: str,
        lines: list[dict[str, Any]],
    ) -> Subscription:
        """
        Create a new draft subscription.

        Validates:
        - Customer exists and belongs to tenant
        - Plan exists and belongs to tenant
        - At least one line item
        - start_date < expiry_date
        """
        await self._validate_customer(customer_id)
        await self._validate_plan(plan_id)
        self._validate_dates(start_date, expiry_date)
        self._validate_lines(lines)

        number = await self._next_number()

        sub = await self.repo.create(
            {
                "number": number,
                "customer_id": customer_id,
                "plan_id": plan_id,
                "start_date": start_date,
                "expiry_date": expiry_date,
                "payment_terms": payment_terms,
                "status": SubscriptionStatus.DRAFT,
            }
        )

        await self._create_lines(sub.id, lines)
        await self.db.refresh(sub)
        event_bus.emit("subscription.created", sub)
        return sub

    # ── STATUS TRANSITIONS ───────────────────────────────────────

    async def activate(self, sub_id: uuid.UUID) -> Subscription:
        """
        Move subscription to the next state toward ACTIVE.

        draft → quotation → confirmed → active
        Generates an invoice when moving to active.
        """
        sub = await self.repo.find_by_id(sub_id)
        target = self._next_activation_status(sub.status)
        SubscriptionStatusFSM.transition(sub, target)

        if target == SubscriptionStatus.ACTIVE:
            await InvoiceFactory.create_from_subscription(
                self.db, sub, self.tenant_id
            )
            event_bus.emit("subscription.activated", sub)

        await self.db.flush()
        await self.db.refresh(sub)
        return sub

    async def close(self, sub_id: uuid.UUID) -> Subscription:
        """Close an active subscription."""
        sub = await self._load_with_plan(sub_id)
        SubscriptionStatusFSM.transition(sub, SubscriptionStatus.CLOSED)
        await self.db.flush()
        await self.db.refresh(sub)
        event_bus.emit("subscription.closed", sub)
        return sub

    # ── BULK ─────────────────────────────────────────────────────

    async def bulk_create(
        self,
        items: list[dict[str, Any]],
    ) -> list[Subscription]:
        """Create multiple subscriptions in a single transaction."""
        results: list[Subscription] = []
        for item in items:
            sub = await self.create(
                customer_id=item["customer_id"],
                plan_id=item["plan_id"],
                start_date=item["start_date"],
                expiry_date=item["expiry_date"],
                payment_terms=item.get("payment_terms", "net-30"),
                lines=item["lines"],
            )
            results.append(sub)
        return results

    # ── UPDATE (PATCH) ───────────────────────────────────────────

    async def update(
        self,
        sub_id: uuid.UUID,
        data: dict[str, Any],
    ) -> Subscription:
        """Update mutable fields on a draft/quotation subscription."""
        sub = await self.repo.find_by_id(sub_id)
        if sub.status not in (
            SubscriptionStatus.DRAFT,
            SubscriptionStatus.QUOTATION,
        ):
            raise ConflictException(
                "Only draft or quotation subscriptions can be edited."
            )

        allowed = {"payment_terms", "start_date", "expiry_date"}
        update_data = {k: v for k, v in data.items() if k in allowed}
        if update_data:
            entity = await self.repo.update(sub_id, update_data)
            return entity
        return sub

    # ═══════════════════════════════════════════════════════════════
    # Private helpers
    # ═══════════════════════════════════════════════════════════════

    async def _validate_customer(self, customer_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(User.id).where(
                User.id == customer_id,
                User.tenant_id == self.tenant_id,
                User.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundException(f"Customer {customer_id} not found.")

    async def _validate_plan(self, plan_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Plan.id).where(
                Plan.id == plan_id,
                Plan.tenant_id == self.tenant_id,
                Plan.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundException(f"Plan {plan_id} not found.")

    @staticmethod
    def _validate_dates(start: date, expiry: date) -> None:
        if expiry <= start:
            raise ValidationException(
                [{"field": "expiry_date", "message": "Must be after start_date."}]
            )

    @staticmethod
    def _validate_lines(lines: list[dict[str, Any]]) -> None:
        if not lines:
            raise ValidationException(
                [{"field": "lines", "message": "At least one line required."}]
            )

    async def _next_number(self) -> str:
        """Generate next sequential subscription number for tenant."""
        result = await self.db.execute(
            select(func.count()).select_from(Subscription).where(
                Subscription.tenant_id == self.tenant_id,
            )
        )
        count = result.scalar_one()
        return f"SUB-{count + 1:06d}"

    async def _create_lines(
        self,
        subscription_id: uuid.UUID,
        lines: list[dict[str, Any]],
    ) -> None:
        """Create subscription line items."""
        line_repo: BaseRepository[SubscriptionLine] = BaseRepository(
            self.db, self.tenant_id,
        )
        line_repo.model = SubscriptionLine
        for ln in lines:
            await line_repo.create(
                {
                    "subscription_id": subscription_id,
                    "product_id": ln["product_id"],
                    "qty": ln.get("qty", 1),
                    "unit_price": Decimal(str(ln["unit_price"])),
                    "tax_ids": ln.get("tax_ids"),
                }
            )

    async def _load_with_plan(self, sub_id: uuid.UUID) -> Subscription:
        """Load subscription with plan relationship for FSM guards."""
        query = (
            select(Subscription)
            .options(selectinload(Subscription.lines))
            .where(
                Subscription.id == sub_id,
                Subscription.tenant_id == self.tenant_id,
                Subscription.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        sub = result.scalar_one_or_none()
        if sub is None:
            raise NotFoundException(f"Subscription {sub_id} not found.")
        # Eagerly load the plan for FSM closable guard
        plan_result = await self.db.execute(
            select(Plan).where(Plan.id == sub.plan_id)
        )
        sub.plan = plan_result.scalar_one_or_none()  # type: ignore[attr-defined]
        return sub

    @staticmethod
    def _next_activation_status(
        current: SubscriptionStatus,
    ) -> SubscriptionStatus:
        """Determine the next step toward ACTIVE."""
        path = {
            SubscriptionStatus.DRAFT: SubscriptionStatus.QUOTATION,
            SubscriptionStatus.QUOTATION: SubscriptionStatus.CONFIRMED,
            SubscriptionStatus.CONFIRMED: SubscriptionStatus.ACTIVE,
        }
        target = path.get(current)
        if target is None:
            raise ConflictException(
                f"Subscription in state '{current.value}' cannot be activated."
            )
        return target
