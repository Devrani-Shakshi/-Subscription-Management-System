"""
PortalSubscriptionService — self-service for portal_user.

Routes:
  GET   /portal/my-subscription
  GET   /portal/my-subscription/change-plan/preview
  POST  /portal/my-subscription/change-plan
  POST  /portal/my-subscription/cancel
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import InvoiceStatus, SubscriptionStatus
from app.exceptions.base import ConflictException, NotFoundException
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.services.subscriptions.downgrade import DowngradeService
from app.services.subscriptions.event_bus import event_bus
from app.services.subscriptions.fsm import SubscriptionStatusFSM
from app.services.subscriptions.pro_rata import ProRataCalculator
from app.services.subscriptions.upgrade import UpgradeService


class PortalSubscriptionService:
    """Portal user self-service subscription operations."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    # ── GET MY SUBSCRIPTION ─────────────────────────────────────

    async def get_my_subscription(self) -> dict[str, Any]:
        """
        Return the portal user's active subscription with:
        - Plan card info
        - Order lines
        - Last 3 invoices
        """
        sub = await self._require_own_subscription()
        plan = await self._load_plan(sub.plan_id)
        invoices = await self._recent_invoices(sub.id, limit=3)

        lines = [
            {
                "product_id": str(ln.product_id),
                "qty": ln.qty,
                "unit_price": str(ln.unit_price),
                "line_total": str(ln.unit_price * ln.qty),
            }
            for ln in sub.lines
        ]

        invoice_list = [
            {
                "id": str(inv.id),
                "status": inv.status.value,
                "total": str(inv.total),
                "due_date": inv.due_date.isoformat(),
            }
            for inv in invoices
        ]

        return {
            "subscription": {
                "id": str(sub.id),
                "number": sub.number,
                "status": sub.status.value,
                "start_date": sub.start_date.isoformat(),
                "expiry_date": sub.expiry_date.isoformat(),
                "payment_terms": sub.payment_terms,
            },
            "plan": {
                "id": str(plan.id),
                "name": plan.name,
                "price": str(plan.price),
                "billing_period": plan.billing_period.value,
            },
            "lines": lines,
            "recent_invoices": invoice_list,
        }

    # ── CHANGE PLAN PREVIEW ─────────────────────────────────────

    async def change_plan_preview(
        self, target_plan_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Preview what happens if the user switches to target_plan_id.

        Returns:
        - amount_due_today (upgrade) or 0 (downgrade)
        - pro_rata_days
        - effective_date
        - direction: 'upgrade' | 'downgrade'
        """
        sub = await self._require_own_subscription()
        current_plan = await self._load_plan(sub.plan_id)
        target_plan = await self._load_plan(target_plan_id)

        billing_days = ProRataCalculator.billing_cycle_days(
            sub.start_date, sub.expiry_date,
        )
        remaining_days = ProRataCalculator.remaining_days_in_cycle(
            sub.start_date, sub.expiry_date,
        )

        is_upgrade = target_plan.price > current_plan.price

        if is_upgrade:
            pro_rata = ProRataCalculator.calculate(
                current_plan.price,
                target_plan.price,
                billing_days,
                remaining_days,
            )
            return {
                "direction": "upgrade",
                "amount_due_today": str(pro_rata.amount_due),
                "pro_rata_days": remaining_days,
                "effective_date": date.today().isoformat(),
            }

        return {
            "direction": "downgrade",
            "amount_due_today": "0.00",
            "pro_rata_days": remaining_days,
            "effective_date": sub.expiry_date.isoformat(),
        }

    # ── CHANGE PLAN ─────────────────────────────────────────────

    async def change_plan(
        self, target_plan_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Execute a plan change.

        Upgrade: immediate via UpgradeService
        Downgrade: scheduled via DowngradeService
        """
        sub = await self._require_own_subscription()
        current_plan = await self._load_plan(sub.plan_id)
        target_plan = await self._load_plan(target_plan_id)

        if target_plan.price > current_plan.price:
            svc = UpgradeService(self.db, self.tenant_id)
            return await svc.execute(sub.id, target_plan_id)

        svc_down = DowngradeService(self.db, self.tenant_id)
        return await svc_down.execute(sub.id, target_plan_id)

    # ── CANCEL ──────────────────────────────────────────────────

    async def cancel(
        self, reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel the portal user's subscription.

        Respects FSM + closable flag guard.
        """
        sub = await self._require_own_subscription()

        # Eagerly attach plan for closable guard
        plan = await self._load_plan(sub.plan_id)
        sub.plan = plan  # type: ignore[attr-defined]

        SubscriptionStatusFSM.transition(sub, SubscriptionStatus.CLOSED)
        await self.db.flush()
        await self.db.refresh(sub)

        event_bus.emit("subscription.cancelled", sub, reason)

        return {
            "subscription_id": str(sub.id),
            "status": sub.status.value,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════
    # Private helpers
    # ═══════════════════════════════════════════════════════════════

    async def _require_own_subscription(self) -> Subscription:
        """
        OwnershipGuard: ensure portal_user has a subscription
        and it belongs to them.
        """
        query = (
            select(Subscription)
            .options(selectinload(Subscription.lines))
            .where(
                Subscription.customer_id == self.user_id,
                Subscription.tenant_id == self.tenant_id,
                Subscription.deleted_at.is_(None),
                Subscription.status.in_(
                    [
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.CONFIRMED,
                        SubscriptionStatus.DRAFT,
                        SubscriptionStatus.QUOTATION,
                    ]
                ),
            )
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        sub = result.scalar_one_or_none()
        if sub is None:
            raise NotFoundException("No active subscription.")
        return sub

    async def _load_plan(self, plan_id: uuid.UUID) -> Plan:
        result = await self.db.execute(
            select(Plan).where(
                Plan.id == plan_id,
                Plan.deleted_at.is_(None),
            )
        )
        plan = result.scalar_one_or_none()
        if plan is None:
            raise NotFoundException(f"Plan {plan_id} not found.")
        return plan

    async def _recent_invoices(
        self, subscription_id: uuid.UUID, limit: int = 3,
    ) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice)
            .where(
                Invoice.subscription_id == subscription_id,
                Invoice.tenant_id == self.tenant_id,
                Invoice.deleted_at.is_(None),
            )
            .order_by(Invoice.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
