"""
Discount strategies — Strategy pattern for applying discounts.

Each strategy implements :meth:`apply` to reduce a subtotal
by either a fixed amount or a percentage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import ROUND_HALF_UP, Decimal

from app.core.enums import DiscountType
from app.models.discount import Discount


class DiscountStrategy(ABC):
    """Abstract base for all discount calculation strategies."""

    @abstractmethod
    def apply(self, subtotal: Decimal, discount: Discount) -> Decimal:
        """
        Calculate the discount amount (positive value to subtract).

        Parameters
        ----------
        subtotal:
            The pre-discount subtotal.
        discount:
            The Discount ORM model with type, value, limits, etc.

        Returns
        -------
        Decimal
            The amount to subtract from subtotal.
        """


class FixedDiscountStrategy(DiscountStrategy):
    """Subtract a fixed monetary amount."""

    def apply(self, subtotal: Decimal, discount: Discount) -> Decimal:
        amount = min(discount.value, subtotal)
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class PercentDiscountStrategy(DiscountStrategy):
    """Subtract a percentage of the subtotal."""

    def apply(self, subtotal: Decimal, discount: Discount) -> Decimal:
        amount = subtotal * discount.value / Decimal("100")
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class DiscountStrategyFactory:
    """
    Factory to select the correct discount strategy.

    Usage::

        strategy = DiscountStrategyFactory.create(discount.type)
        discount_amount = strategy.apply(subtotal, discount)
    """

    _strategies: dict[DiscountType, DiscountStrategy] = {
        DiscountType.FIXED: FixedDiscountStrategy(),
        DiscountType.PERCENT: PercentDiscountStrategy(),
    }

    @staticmethod
    def create(discount_type: DiscountType) -> DiscountStrategy:
        strategy = DiscountStrategyFactory._strategies.get(discount_type)
        if strategy is None:
            raise ValueError(
                f"Unknown discount type: {discount_type.value}"
            )
        return strategy
