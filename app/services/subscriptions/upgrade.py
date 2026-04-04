"""
UpgradeService — immediate plan upgrade with pro-rata delta invoice.

Path: /company/subscriptions/{id}/upgrade
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository
from app.services.subscriptions.event_bus import event_bus
from app.services.subscriptions.invoice_factory import InvoiceFactory
from app.services.subscriptions.pro_rata import ProRataCalculator


class UpgradeService:
    """Handle immediate plan upgrades with pro-rata billing."""

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

    async def execute(
        self,
        subscription_id: uuid.UUID,
        new_plan_id: uuid.UUID,
    ) -> dict:
        """
        Upgrade subscription to a new plan immediately.

        Steps:
        1. Validate subscription exists and is active
        2. Validate new plan exists and is different
        3. Compute pro-rata amount
        4. Create delta invoice
        5. Update plan_id
        6. Emit event

        Returns dict with subscription + delta invoice info.
        """
        sub = await self.repo.find_by_id(subscription_id)
        self._validate_active(sub)

        if sub.plan_id == new_plan_id:
            raise ConflictException("Already on this plan.")

        old_plan = await self._load_plan(sub.plan_id)
        new_plan = await self._load_plan(new_plan_id)

        billing_days = ProRataCalculator.billing_cycle_days(
            sub.start_date, sub.expiry_date
        )
        remaining_days = ProRataCalculator.remaining_days_in_cycle(
            sub.start_date, sub.expiry_date
        )

        pro_rata = ProRataCalculator.calculate(
            old_price=old_plan.price,
            new_price=new_plan.price,
            billing_days=billing_days,
            remaining_days=remaining_days,
        )

        delta_invoice = await InvoiceFactory.create_delta(
            self.db, sub, pro_rata, self.tenant_id
        )

        sub.plan_id = new_plan_id
        await self.db.flush()
        await self.db.refresh(sub)

        event_bus.emit("subscription.upgraded", sub)

        return {
            "subscription": sub.to_dict(),
            "delta_invoice_id": str(delta_invoice.id),
            "amount_due": str(pro_rata.amount_due),
            "remaining_days": pro_rata.remaining_days,
        }

    # ── Private ──────────────────────────────────────────────────

    @staticmethod
    def _validate_active(sub: Subscription) -> None:
        from app.core.enums import SubscriptionStatus

        if sub.status != SubscriptionStatus.ACTIVE:
            raise ConflictException(
                "Only active subscriptions can be upgraded."
            )

    async def _load_plan(self, plan_id: uuid.UUID) -> Plan:
        result = await self.db.execute(
            select(Plan).where(
                Plan.id == plan_id,
                Plan.tenant_id == self.tenant_id,
                Plan.deleted_at.is_(None),
            )
        )
        plan = result.scalar_one_or_none()
        if plan is None:
            raise NotFoundException(f"Plan {plan_id} not found.")
        return plan
