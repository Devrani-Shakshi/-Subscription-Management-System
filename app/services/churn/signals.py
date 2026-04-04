"""
Churn prediction signals — OCP-compliant signal classes.

Each signal implements the ``compute`` method and returns a
``SignalResult`` indicating whether the signal was triggered
and its weight contribution to the total churn score.

Adding a new signal: create a new class inheriting ``ChurnSignal``
and register it in the engine's signal list. No existing code changes.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    DunningStatus,
    InvoiceStatus,
    SubscriptionStatus,
)

if TYPE_CHECKING:
    from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SignalResult:
    """Outcome of a single churn signal evaluation."""

    key: str
    weight: int
    triggered: bool
    detail: str = ""


class ChurnSignal(ABC):
    """Abstract churn signal — one per risk factor."""

    @abstractmethod
    async def compute(
        self, customer: "User", db: AsyncSession
    ) -> SignalResult:
        """Evaluate this signal for a given customer."""
        ...


# ═══════════════════════════════════════════════════════════════
# Concrete Signals
# ═══════════════════════════════════════════════════════════════


class LoginInactivitySignal(ChurnSignal):
    """Triggered when customer hasn't logged in for > 14 days."""

    THRESHOLD_DAYS = 14
    WEIGHT = 20

    async def compute(
        self, customer: "User", db: AsyncSession
    ) -> SignalResult:
        from app.models.session import Session as SessionModel

        query = (
            select(func.max(SessionModel.created_at))
            .where(SessionModel.user_id == customer.id)
        )
        result = await db.execute(query)
        last_login = result.scalar_one_or_none()

        if last_login is None:
            return SignalResult(
                key="login_inactivity",
                weight=self.WEIGHT,
                triggered=True,
                detail="No login history found.",
            )

        now = datetime.now(timezone.utc)
        # Handle timezone-naive datetimes from SQLite tests
        if last_login.tzinfo is None:
            last_login = last_login.replace(tzinfo=timezone.utc)
        days_since = (now - last_login).days
        triggered = days_since > self.THRESHOLD_DAYS

        return SignalResult(
            key="login_inactivity",
            weight=self.WEIGHT,
            triggered=triggered,
            detail=f"{days_since} days since last login.",
        )


class OverdueInvoiceSignal(ChurnSignal):
    """Triggered when customer has > 1 overdue invoice."""

    THRESHOLD = 1
    WEIGHT = 30

    async def compute(
        self, customer: "User", db: AsyncSession
    ) -> SignalResult:
        from app.models.invoice import Invoice

        query = (
            select(func.count())
            .select_from(Invoice)
            .where(
                and_(
                    Invoice.customer_id == customer.id,
                    Invoice.status == InvoiceStatus.OVERDUE,
                    Invoice.deleted_at.is_(None),
                )
            )
        )
        result = await db.execute(query)
        count = result.scalar_one()
        triggered = count > self.THRESHOLD

        return SignalResult(
            key="overdue_invoices",
            weight=self.WEIGHT,
            triggered=triggered,
            detail=f"{count} overdue invoice(s).",
        )


class DowngradeSignal(ChurnSignal):
    """Triggered when customer downgraded in the last 30 days."""

    LOOKBACK_DAYS = 30
    WEIGHT = 25

    async def compute(
        self, customer: "User", db: AsyncSession
    ) -> SignalResult:
        from app.models.subscription import Subscription

        cutoff = datetime.now(timezone.utc) - timedelta(
            days=self.LOOKBACK_DAYS
        )

        query = (
            select(func.count())
            .select_from(Subscription)
            .where(
                and_(
                    Subscription.customer_id == customer.id,
                    Subscription.downgrade_at.isnot(None),
                    Subscription.downgrade_at >= cutoff,
                    Subscription.deleted_at.is_(None),
                )
            )
        )
        result = await db.execute(query)
        count = result.scalar_one()
        triggered = count > 0

        return SignalResult(
            key="recent_downgrade",
            weight=self.WEIGHT,
            triggered=triggered,
            detail=f"{count} downgrade(s) in last 30 days.",
        )


class PausedSignal(ChurnSignal):
    """Triggered when customer has a paused subscription."""

    WEIGHT = 40

    async def compute(
        self, customer: "User", db: AsyncSession
    ) -> SignalResult:
        from app.models.subscription import Subscription

        query = (
            select(func.count())
            .select_from(Subscription)
            .where(
                and_(
                    Subscription.customer_id == customer.id,
                    Subscription.status == SubscriptionStatus.PAUSED,
                    Subscription.deleted_at.is_(None),
                )
            )
        )
        result = await db.execute(query)
        count = result.scalar_one()
        triggered = count > 0

        return SignalResult(
            key="paused_subscription",
            weight=self.WEIGHT,
            triggered=triggered,
            detail=f"{count} paused subscription(s).",
        )


class DunningSignal(ChurnSignal):
    """Triggered when customer has an active dunning schedule."""

    WEIGHT = 35

    async def compute(
        self, customer: "User", db: AsyncSession
    ) -> SignalResult:
        from app.models.dunning_schedule import DunningSchedule
        from app.models.invoice import Invoice

        query = (
            select(func.count())
            .select_from(DunningSchedule)
            .join(Invoice, DunningSchedule.invoice_id == Invoice.id)
            .where(
                and_(
                    Invoice.customer_id == customer.id,
                    DunningSchedule.status == DunningStatus.PENDING,
                    DunningSchedule.deleted_at.is_(None),
                )
            )
        )
        result = await db.execute(query)
        count = result.scalar_one()
        triggered = count > 0

        return SignalResult(
            key="active_dunning",
            weight=self.WEIGHT,
            triggered=triggered,
            detail=f"{count} active dunning schedule(s).",
        )
