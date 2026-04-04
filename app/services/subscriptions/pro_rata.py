"""
ProRataCalculator — strategy for computing upgrade/downgrade pro-rata amounts.

Stateless utility: all methods are classmethods.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class ProRataResult:
    """Immutable result of a pro-rata calculation."""

    old_daily_rate: Decimal
    new_daily_rate: Decimal
    remaining_days: int
    billing_days: int
    credit: Decimal
    charge: Decimal
    amount_due: Decimal


class ProRataCalculator:
    """Calculate pro-rata charges for plan changes."""

    @classmethod
    def calculate(
        cls,
        old_price: Decimal,
        new_price: Decimal,
        billing_days: int,
        remaining_days: int,
    ) -> ProRataResult:
        """
        Compute the net amount due on a mid-cycle plan switch.

        Parameters
        ----------
        old_price : Full-cycle price of the current plan.
        new_price : Full-cycle price of the new plan.
        billing_days : Total days in the billing cycle.
        remaining_days : Days left in the current cycle.

        Returns
        -------
        ProRataResult with credit, charge, and net amount_due.
        """
        if billing_days <= 0:
            billing_days = 1  # prevent division by zero

        old_daily = (old_price / billing_days).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        new_daily = (new_price / billing_days).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        credit = (old_daily * remaining_days).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        charge = (new_daily * remaining_days).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        amount_due = (charge - credit).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return ProRataResult(
            old_daily_rate=old_daily,
            new_daily_rate=new_daily,
            remaining_days=remaining_days,
            billing_days=billing_days,
            credit=credit,
            charge=charge,
            amount_due=max(amount_due, Decimal("0.00")),
        )

    @classmethod
    def remaining_days_in_cycle(
        cls,
        start_date: date,
        expiry_date: date,
        today: date | None = None,
    ) -> int:
        """Return number of days remaining in the current billing cycle."""
        today = today or date.today()
        remaining = (expiry_date - today).days
        return max(remaining, 0)

    @classmethod
    def billing_cycle_days(
        cls,
        start_date: date,
        expiry_date: date,
    ) -> int:
        """Return total days in the billing cycle."""
        return max((expiry_date - start_date).days, 1)
