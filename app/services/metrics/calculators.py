"""
Metric calculators — abstract base + concrete KPI implementations.

Each calculator follows OOP: inherit ``MetricCalculator``, implement
``calculate()``, return ``MetricResult``.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus, SubscriptionStatus, UserRole
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User


@dataclass(frozen=True)
class DateRange:
    """Date range for metric computation."""

    start: date
    end: date


@dataclass
class MetricResult:
    """Result of a metric calculation."""

    name: str
    value: str
    raw_value: Decimal
    trend: str = "flat"  # "up" | "down" | "flat"
    delta: str = ""
    period: str = ""


class MetricCalculator(ABC):
    """Abstract metric calculator."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: Optional[uuid.UUID],
        date_range: DateRange,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.date_range = date_range

    def _tenant_filter(self, model):
        """Apply tenant filter if tenant_id is set."""
        if self.tenant_id is not None:
            return model.tenant_id == self.tenant_id
        return True  # No filter for super_admin

    @abstractmethod
    async def calculate(self) -> MetricResult:
        """Compute the metric."""
        ...


class MRRCalculator(MetricCalculator):
    """Monthly Recurring Revenue — sum of active subscription plan prices."""

    async def calculate(self) -> MetricResult:
        from app.models.plan import Plan

        query = (
            select(func.coalesce(func.sum(Plan.price), 0))
            .select_from(Subscription)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.deleted_at.is_(None),
                    self._tenant_filter(Subscription),
                )
            )
        )
        result = await self.db.execute(query)
        mrr = Decimal(str(result.scalar_one()))

        return MetricResult(
            name="MRR",
            value=f"${mrr:,.2f}",
            raw_value=mrr,
            period=f"{self.date_range.start} – {self.date_range.end}",
        )


class ARRCalculator(MetricCalculator):
    """Annual Recurring Revenue — MRR × 12."""

    async def calculate(self) -> MetricResult:
        mrr_calc = MRRCalculator(
            self.db, self.tenant_id, self.date_range
        )
        mrr_result = await mrr_calc.calculate()
        arr = mrr_result.raw_value * 12

        return MetricResult(
            name="ARR",
            value=f"${arr:,.2f}",
            raw_value=arr,
            period=mrr_result.period,
        )


class NRRCalculator(MetricCalculator):
    """
    Net Revenue Retention — revenue from existing customers
    after expansions and contractions.

    Formula: (MRR_end - new_MRR) / MRR_start × 100
    Simplified: uses payments from existing customers.
    """

    async def calculate(self) -> MetricResult:
        # Current period payments
        current_q = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .select_from(Payment)
            .where(
                and_(
                    Payment.deleted_at.is_(None),
                    self._tenant_filter(Payment),
                )
            )
        )
        current = Decimal(
            str((await self.db.execute(current_q)).scalar_one())
        )

        # Previous period. If no data, NRR = 100%
        nrr = Decimal("100.00") if current == 0 else Decimal("100.00")
        if current > 0:
            # Simplified: assume NRR is based on ratio of
            # active subs to total subs
            active_q = (
                select(func.count())
                .select_from(Subscription)
                .where(
                    and_(
                        Subscription.status == SubscriptionStatus.ACTIVE,
                        Subscription.deleted_at.is_(None),
                        self._tenant_filter(Subscription),
                    )
                )
            )
            total_q = (
                select(func.count())
                .select_from(Subscription)
                .where(
                    and_(
                        Subscription.deleted_at.is_(None),
                        self._tenant_filter(Subscription),
                    )
                )
            )
            active = (await self.db.execute(active_q)).scalar_one()
            total = (await self.db.execute(total_q)).scalar_one()
            if total > 0:
                nrr = (Decimal(str(active)) / Decimal(str(total)) * 100
                       ).quantize(Decimal("0.01"))

        return MetricResult(
            name="NRR",
            value=f"{nrr}%",
            raw_value=nrr,
        )


class ChurnRateCalculator(MetricCalculator):
    """
    Customer churn rate — percentage of closed subscriptions
    relative to total subscriptions.
    """

    async def calculate(self) -> MetricResult:
        closed_q = (
            select(func.count())
            .select_from(Subscription)
            .where(
                and_(
                    Subscription.status == SubscriptionStatus.CLOSED,
                    Subscription.deleted_at.is_(None),
                    self._tenant_filter(Subscription),
                )
            )
        )
        total_q = (
            select(func.count())
            .select_from(Subscription)
            .where(
                and_(
                    Subscription.deleted_at.is_(None),
                    self._tenant_filter(Subscription),
                )
            )
        )

        closed = (await self.db.execute(closed_q)).scalar_one()
        total = (await self.db.execute(total_q)).scalar_one()

        rate = Decimal("0")
        if total > 0:
            rate = (Decimal(str(closed)) / Decimal(str(total)) * 100
                    ).quantize(Decimal("0.01"))

        return MetricResult(
            name="Churn Rate",
            value=f"{rate}%",
            raw_value=rate,
        )


class LTVCalculator(MetricCalculator):
    """
    Customer Lifetime Value — average revenue per customer ÷ churn rate.

    LTV = ARPU / churn_rate (if churn_rate > 0).
    """

    async def calculate(self) -> MetricResult:
        # Average revenue per user
        rev_q = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .select_from(Payment)
            .where(
                and_(
                    Payment.deleted_at.is_(None),
                    self._tenant_filter(Payment),
                )
            )
        )
        total_rev = Decimal(
            str((await self.db.execute(rev_q)).scalar_one())
        )

        customer_q = (
            select(func.count())
            .select_from(User)
            .where(
                and_(
                    User.role == UserRole.PORTAL_USER,
                    User.deleted_at.is_(None),
                )
            )
        )
        if self.tenant_id:
            customer_q = customer_q.where(
                User.tenant_id == self.tenant_id
            )
        customers = (await self.db.execute(customer_q)).scalar_one()

        if customers == 0:
            ltv = Decimal("0")
        else:
            arpu = total_rev / customers
            # Get churn rate
            churn_calc = ChurnRateCalculator(
                self.db, self.tenant_id, self.date_range
            )
            churn_result = await churn_calc.calculate()
            churn_rate = churn_result.raw_value

            if churn_rate > 0:
                ltv = (arpu / (churn_rate / 100)).quantize(
                    Decimal("0.01")
                )
            else:
                ltv = arpu * 12  # Default: 12 months

        return MetricResult(
            name="LTV",
            value=f"${ltv:,.2f}",
            raw_value=ltv,
        )
