"""
Churn score engine — aggregates all signal weights into a 0-100 score.

The engine is fault-tolerant: if a signal raises an exception,
it logs a warning and continues with remaining signals.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.churn.signals import ChurnSignal, SignalResult

if TYPE_CHECKING:
    from app.models.user import User

logger = logging.getLogger(__name__)


class ChurnScoreEngine:
    """
    Aggregate churn scorer.

    Iterates through registered signals, sums triggered weights,
    caps the final score at 100.
    """

    def __init__(self, signals: list[ChurnSignal]) -> None:
        self._signals = signals

    async def score(
        self, customer: "User", db: AsyncSession
    ) -> tuple[int, list[dict]]:
        """
        Compute churn score for a customer.

        Returns
        -------
        tuple[int, list[dict]]
            (score 0-100, list of signal breakdown dicts)
        """
        total = 0
        breakdown: list[dict] = []

        for signal in self._signals:
            try:
                result: SignalResult = await signal.compute(customer, db)
                breakdown.append(
                    {
                        "key": result.key,
                        "weight": result.weight,
                        "triggered": result.triggered,
                        "detail": result.detail,
                    }
                )
                if result.triggered:
                    total += result.weight
            except Exception as e:
                logger.warning(
                    "Signal %s failed: %s",
                    signal.__class__.__name__,
                    str(e),
                )
                breakdown.append(
                    {
                        "key": signal.__class__.__name__,
                        "weight": 0,
                        "triggered": False,
                        "detail": f"Error: {e}",
                    }
                )

        return min(total, 100), breakdown
