"""
DowngradeService — scheduled plan downgrade at period end.

Path: /company/subscriptions/{id}/downgrade

The downgrade is NOT applied immediately. Instead:
  sub.downgrade_at = current_period_end_date(sub)
  sub.downgrade_to_plan_id = new_plan_id

A Celery beat task (process_scheduled_downgrades) picks this up
hourly and finalises the change.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SubscriptionStatus
from app.exceptions.base import ConflictException, NotFoundException
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository
from app.services.subscriptions.event_bus import event_bus


class DowngradeService:
    """Schedule a plan downgrade at the end of the current billing period."""

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.repo = self._make_repo()

    def _make_repo(self) -> BaseRepository[Subscription]:
        repo: BaseRepository[Subscription] = BaseRepository(
            self.db, self.tenant_id,
        )
        repo.model = Subscription
        return repo

    async def execute(
        self,
        subscription_id: uuid.UUID,
        new_plan_id: uuid.UUID,
    ) -> dict:
        """
        Schedule a downgrade.

        Guards:
        - Subscription must be active
        - No existing pending downgrade
        - New plan must exist and differ from current
        """
        sub = await self.repo.find_by_id(subscription_id)
        self._validate_active(sub)

        if sub.downgrade_at is not None:
            raise ConflictException(
                f"Plan change already scheduled for "
                f"{sub.downgrade_at.date()}. Cancel it first."
            )

        if sub.plan_id == new_plan_id:
            raise ConflictException("Already on this plan.")

        await self._validate_plan(new_plan_id)

        # Schedule downgrade at expiry_date
        downgrade_at = datetime(
            sub.expiry_date.year,
            sub.expiry_date.month,
            sub.expiry_date.day,
            tzinfo=timezone.utc,
        )
        sub.downgrade_at = downgrade_at
        sub.downgrade_to_plan_id = new_plan_id
        await self.db.flush()
        await self.db.refresh(sub)

        event_bus.emit("subscription.downgrade_scheduled", sub)

        return {
            "subscription": sub.to_dict(),
            "downgrade_at": sub.downgrade_at.isoformat(),
            "downgrade_to_plan_id": str(new_plan_id),
        }

    async def finalize(self, sub: Subscription) -> None:
        """
        Apply the scheduled downgrade.

        Called by Celery beat task when downgrade_at <= now.
        """
        if sub.downgrade_to_plan_id is None:
            return

        sub.plan_id = sub.downgrade_to_plan_id
        sub.downgrade_at = None
        sub.downgrade_to_plan_id = None
        await self.db.flush()

        event_bus.emit("subscription.downgraded", sub)

    # ── Private ──────────────────────────────────────────────────

    @staticmethod
    def _validate_active(sub: Subscription) -> None:
        if sub.status != SubscriptionStatus.ACTIVE:
            raise ConflictException(
                "Only active subscriptions can be downgraded."
            )

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
