"""
Revenue recognition strategies — Strategy pattern.

``RecognitionStrategy`` (ABC) defines the interface.
Concrete strategies produce ``RevenueRecognitionRow`` dataclasses
that are persisted by the service layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    from app.models.invoice import Invoice


@dataclass(frozen=True)
class RevenueRecognitionRow:
    """One period of recognized revenue."""

    recognized_amount: Decimal
    recognition_date: date
    period: str  # e.g. "2026-01"


class RecognitionStrategy(ABC):
    """Abstract strategy for revenue recognition."""

    @abstractmethod
    def recognize(self, invoice: "Invoice") -> list[RevenueRecognitionRow]:
        """Produce recognition rows for the given invoice."""
        ...


class RatableRecognitionStrategy(RecognitionStrategy):
    """
    Splits total evenly across billing periods.

    Uses the subscription's start_date → expiry_date to derive
    the number of monthly periods. Revenue is distributed equally.
    """

    def recognize(self, invoice: "Invoice") -> list[RevenueRecognitionRow]:
        from app.models.invoice import Invoice

        total = invoice.total
        if total <= 0:
            return []

        # Derive period from subscription or default to 1 month
        start = invoice.due_date
        # Default: recognize over 12 months if no sub context
        months = 12

        rows: list[RevenueRecognitionRow] = []
        per_month = (total / months).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        remainder = total - (per_month * months)

        current = start
        for i in range(months):
            amount = per_month
            if i == months - 1:
                amount += remainder  # last month absorbs rounding

            rows.append(
                RevenueRecognitionRow(
                    recognized_amount=amount,
                    recognition_date=current,
                    period=current.strftime("%Y-%m"),
                )
            )
            current = current + relativedelta(months=1)

        return rows


class MilestoneRecognitionStrategy(RecognitionStrategy):
    """
    Recognizes full amount on a specific date (one-time items).

    Used for one-time charges or setup fees that are recognized
    immediately upon invoice confirmation.
    """

    def recognize(self, invoice: "Invoice") -> list[RevenueRecognitionRow]:
        if invoice.total <= 0:
            return []

        return [
            RevenueRecognitionRow(
                recognized_amount=invoice.total,
                recognition_date=invoice.due_date,
                period=invoice.due_date.strftime("%Y-%m"),
            )
        ]
