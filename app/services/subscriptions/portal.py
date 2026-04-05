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

    # ── CREATE SUBSCRIPTION ─────────────────────────────────────

    async def create_subscription(self, plan_id: uuid.UUID) -> dict[str, Any]:
        """Create a new subscription if the portal user does not have one."""
        query = select(Subscription).where(
            Subscription.customer_id == self.user_id,
            Subscription.tenant_id == self.tenant_id,
            Subscription.status != SubscriptionStatus.CLOSED,
            Subscription.deleted_at.is_(None)
        )
        existing = (await self.db.execute(query)).scalars().first()
        if existing:
            raise ConflictException("You already have an active subscription.")

        plan = await self._load_plan(plan_id)
        
        # Determine dates based on billing period
        import calendar
        start_date = date.today()
        expires = start_date
        from dateutil.relativedelta import relativedelta
        if plan.billing_period.value == "monthly":
            expires = start_date + relativedelta(months=1)
        elif plan.billing_period.value == "quarterly":
            expires = start_date + relativedelta(months=3)
        elif plan.billing_period.value == "yearly":
            expires = start_date + relativedelta(years=1)
            
        import string
        import random
        sub_number = "SUB-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        sub = Subscription(
            tenant_id=self.tenant_id,
            customer_id=self.user_id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=start_date,
            expiry_date=expires,
            payment_terms=plan.billing_period.value,
            number=sub_number
        )
        self.db.add(sub)
        await self.db.flush()

        # Get or create a product representing this plan
        from app.models.product import Product
        product = (await self.db.execute(
            select(Product).where(Product.tenant_id == self.tenant_id, Product.name == plan.name)
        )).scalars().first()
        
        if not product:
            product = Product(
                tenant_id=self.tenant_id,
                name=plan.name,
                type="service",
                sales_price=plan.price,
                cost_price=0
            )
            self.db.add(product)
            await self.db.flush()

        # Add a default line 
        from app.models.subscription_line import SubscriptionLine
        line = SubscriptionLine(  
            tenant_id=self.tenant_id,
            subscription_id=sub.id,
            product_id=product.id,
            qty=1,
            unit_price=plan.price
        )
        self.db.add(line)
        await self.db.flush()

        from sqlalchemy.orm import selectinload
        sub_loaded = (await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.lines))
            .where(Subscription.id == sub.id)
        )).scalars().first()
        
        # Create initial invoice
        from app.services.subscriptions.invoice_factory import InvoiceFactory
        invoice = await InvoiceFactory.create_from_subscription(
            db=self.db,
            sub=sub_loaded,
            tenant_id=self.tenant_id
        )
        invoice.status = InvoiceStatus.CONFIRMED
        await self.db.flush()
        
        return await self.get_my_subscription()

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

        # Get product names using product IDs from lines
        product_dict = {}
        if sub.lines:
            from app.models.product import Product
            product_ids = [ln.product_id for ln in sub.lines]
            products = (await self.db.execute(select(Product).where(Product.id.in_(product_ids)))).scalars()
            product_dict = {p.id: p.name for p in products}

        lines = [
            {
                "id": str(ln.id),
                "product": product_dict.get(ln.product_id, "Service Plan"),
                "quantity": ln.qty,
                "unitPrice": float(ln.unit_price),
                "total": float(ln.unit_price * ln.qty),
            }
            for ln in sub.lines
        ]

        subtotal = sum(ln["total"] for ln in lines)

        invoice_list = [
            {
                "id": str(inv.id),
                "number": inv.invoice_number,
                "date": inv.created_at.isoformat() if inv.created_at else inv.due_date.isoformat(),
                "dueDate": inv.due_date.isoformat(),
                "amount": float(inv.total),
                "status": inv.status.value,
            }
            for inv in invoices
        ]

        return {
            "id": str(sub.id),
            "planId": str(plan.id),
            "planName": plan.name,
            "billingPeriod": plan.billing_period.value,
            "status": sub.status.value,
            "price": float(plan.price),
            "nextBillingDate": sub.expiry_date.isoformat() if sub.expiry_date else "",
            "startDate": sub.start_date.isoformat(),
            "expiryDate": sub.expiry_date.isoformat() if sub.expiry_date else None,
            "orderLines": lines,
            "subtotal": subtotal,
            "tax": 0.0,
            "discount": 0.0,
            "grandTotal": subtotal,
            "recentInvoices": invoice_list,
            "scheduledDowngrade": None,
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
                "todaysCharge": float(pro_rata.amount_due),
                "daysRemaining": remaining_days,
                "newPlanName": target_plan.name,
                "effectiveDate": date.today().isoformat(),
                "warnings": []
            }

        return {
            "direction": "downgrade",
            "todaysCharge": 0.0,
            "daysRemaining": remaining_days,
            "newPlanName": target_plan.name,
            "effectiveDate": sub.expiry_date.isoformat() if sub.expiry_date else "",
            "warnings": [
                "Your current plan features will remain active until the end of the billing cycle.",
                "The new rate will apply on the next billing date."
            ]
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
