"""
Bulk operation abstract base + concrete implementations.

Each operation provides validate() and execute() methods.
Operations are stateless — all state is held in the executor.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SubscriptionStatus
from app.models.subscription import Subscription


@dataclass
class ConflictItem:
    """A single conflict detected during pre-flight check."""

    id: uuid.UUID
    conflict_type: str
    reason: str


@dataclass
class FailedItem:
    """A single failed item during execution."""

    id: uuid.UUID
    reason: str


@dataclass
class ConflictReport:
    """Result of conflict detection — list of conflicts found."""

    conflicts: list[ConflictItem] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0


@dataclass
class BulkResult:
    """Outcome of a bulk operation execution."""

    success: list[uuid.UUID] = field(default_factory=list)
    failed: list[FailedItem] = field(default_factory=list)
    conflicts: list[ConflictItem] = field(default_factory=list)
    total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": [str(s) for s in self.success],
            "failed": [
                {"id": str(f.id), "reason": f.reason}
                for f in self.failed
            ],
            "conflicts": [
                {
                    "id": str(c.id),
                    "conflict_type": c.conflict_type,
                    "reason": c.reason,
                }
                for c in self.conflicts
            ],
            "total": self.total,
            "success_count": len(self.success),
            "failed_count": len(self.failed),
        }


class BulkOperation(ABC):
    """Abstract bulk operation interface."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        params: dict[str, Any] | None = None,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.params = params or {}

    @abstractmethod
    async def validate(self, ids: list[uuid.UUID]) -> ConflictReport:
        """Check for conflicts before execution."""
        ...

    @abstractmethod
    async def execute(self, ids: list[uuid.UUID]) -> BulkResult:
        """Execute the operation on the given IDs."""
        ...

    async def _get_subscriptions(
        self, ids: list[uuid.UUID]
    ) -> list[Subscription]:
        """Fetch subscriptions by IDs within tenant scope."""
        query = (
            select(Subscription)
            .where(
                and_(
                    Subscription.id.in_(ids),
                    Subscription.tenant_id == self.tenant_id,
                    Subscription.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


class BulkActivate(BulkOperation):
    """Activate confirmed subscriptions in bulk."""

    async def validate(self, ids: list[uuid.UUID]) -> ConflictReport:
        report = ConflictReport()
        subs = await self._get_subscriptions(ids)
        found_ids = {s.id for s in subs}

        for sub_id in ids:
            if sub_id not in found_ids:
                report.conflicts.append(
                    ConflictItem(
                        id=sub_id,
                        conflict_type="not_found",
                        reason="Subscription not found.",
                    )
                )

        for sub in subs:
            if sub.status not in (
                SubscriptionStatus.CONFIRMED,
                SubscriptionStatus.PAUSED,
            ):
                report.conflicts.append(
                    ConflictItem(
                        id=sub.id,
                        conflict_type="invalid_status",
                        reason=(
                            f"Cannot activate from '{sub.status.value}'. "
                            "Must be 'confirmed' or 'paused'."
                        ),
                    )
                )

        return report

    async def execute(self, ids: list[uuid.UUID]) -> BulkResult:
        result = BulkResult(total=len(ids))
        subs = await self._get_subscriptions(ids)

        for sub in subs:
            try:
                if sub.status in (
                    SubscriptionStatus.CONFIRMED,
                    SubscriptionStatus.PAUSED,
                ):
                    sub.status = SubscriptionStatus.ACTIVE
                    result.success.append(sub.id)
                else:
                    result.failed.append(
                        FailedItem(
                            id=sub.id,
                            reason=f"Invalid status: {sub.status.value}",
                        )
                    )
            except Exception as e:
                result.failed.append(
                    FailedItem(id=sub.id, reason=str(e))
                )

        await self.db.flush()
        return result


class BulkClose(BulkOperation):
    """Close active/paused subscriptions in bulk."""

    async def validate(self, ids: list[uuid.UUID]) -> ConflictReport:
        report = ConflictReport()
        subs = await self._get_subscriptions(ids)
        found_ids = {s.id for s in subs}

        for sub_id in ids:
            if sub_id not in found_ids:
                report.conflicts.append(
                    ConflictItem(
                        id=sub_id,
                        conflict_type="not_found",
                        reason="Subscription not found.",
                    )
                )

        for sub in subs:
            if sub.status in (
                SubscriptionStatus.CLOSED,
                SubscriptionStatus.DRAFT,
            ):
                report.conflicts.append(
                    ConflictItem(
                        id=sub.id,
                        conflict_type="already_closed",
                        reason=f"Already in '{sub.status.value}' status.",
                    )
                )

        return report

    async def execute(self, ids: list[uuid.UUID]) -> BulkResult:
        result = BulkResult(total=len(ids))
        subs = await self._get_subscriptions(ids)

        for sub in subs:
            try:
                if sub.status not in (
                    SubscriptionStatus.CLOSED,
                    SubscriptionStatus.DRAFT,
                ):
                    sub.status = SubscriptionStatus.CLOSED
                    result.success.append(sub.id)
                else:
                    result.failed.append(
                        FailedItem(
                            id=sub.id,
                            reason=f"Cannot close: {sub.status.value}",
                        )
                    )
            except Exception as e:
                result.failed.append(
                    FailedItem(id=sub.id, reason=str(e))
                )

        await self.db.flush()
        return result


class BulkApplyDiscount(BulkOperation):
    """Apply a discount to multiple subscriptions."""

    async def validate(self, ids: list[uuid.UUID]) -> ConflictReport:
        report = ConflictReport()
        discount_id = self.params.get("discount_id")
        if not discount_id:
            report.conflicts.append(
                ConflictItem(
                    id=uuid.UUID(int=0),
                    conflict_type="missing_param",
                    reason="discount_id is required.",
                )
            )
            return report

        subs = await self._get_subscriptions(ids)
        for sub in subs:
            if sub.discount_id is not None:
                report.conflicts.append(
                    ConflictItem(
                        id=sub.id,
                        conflict_type="already_discounted",
                        reason="Subscription already has a discount.",
                    )
                )

        return report

    async def execute(self, ids: list[uuid.UUID]) -> BulkResult:
        result = BulkResult(total=len(ids))
        discount_id = uuid.UUID(self.params["discount_id"])
        subs = await self._get_subscriptions(ids)

        for sub in subs:
            try:
                sub.discount_id = discount_id
                result.success.append(sub.id)
            except Exception as e:
                result.failed.append(
                    FailedItem(id=sub.id, reason=str(e))
                )

        await self.db.flush()
        return result


class BulkChangePlan(BulkOperation):
    """Change plan for multiple subscriptions."""

    async def validate(self, ids: list[uuid.UUID]) -> ConflictReport:
        report = ConflictReport()
        new_plan_id = self.params.get("plan_id")
        if not new_plan_id:
            report.conflicts.append(
                ConflictItem(
                    id=uuid.UUID(int=0),
                    conflict_type="missing_param",
                    reason="plan_id is required.",
                )
            )
            return report

        subs = await self._get_subscriptions(ids)
        for sub in subs:
            if str(sub.plan_id) == str(new_plan_id):
                report.conflicts.append(
                    ConflictItem(
                        id=sub.id,
                        conflict_type="same_plan",
                        reason="Subscription already on this plan.",
                    )
                )
            if sub.status == SubscriptionStatus.CLOSED:
                report.conflicts.append(
                    ConflictItem(
                        id=sub.id,
                        conflict_type="closed",
                        reason="Cannot change plan on closed subscription.",
                    )
                )

        return report

    async def execute(self, ids: list[uuid.UUID]) -> BulkResult:
        result = BulkResult(total=len(ids))
        new_plan_id = uuid.UUID(self.params["plan_id"])
        subs = await self._get_subscriptions(ids)

        for sub in subs:
            try:
                if sub.status != SubscriptionStatus.CLOSED:
                    sub.plan_id = new_plan_id
                    result.success.append(sub.id)
                else:
                    result.failed.append(
                        FailedItem(
                            id=sub.id,
                            reason="Cannot change plan on closed sub.",
                        )
                    )
            except Exception as e:
                result.failed.append(
                    FailedItem(id=sub.id, reason=str(e))
                )

        await self.db.flush()
        return result
