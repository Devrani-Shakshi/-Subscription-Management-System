"""
Invoice Builder — fluent interface for constructing invoices.

Follows the Builder pattern: construct an Invoice step-by-step
from a subscription's line items, applying discounts and taxes.

Usage::

    builder = InvoiceBuilder(db=session, tenant_id=tenant_id)
    invoice = await (
        builder
        .for_subscription(subscription)
        .add_lines()
        .apply_discount(subscription.discount_id)
        .apply_tax()
        .build()
    )
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus
from app.exceptions.base import NotFoundException, ValidationException
from app.models.discount import Discount
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.subscription import Subscription
from app.models.subscription_line import SubscriptionLine
from app.models.tax import Tax
from app.repositories.billing import (
    DiscountRepository,
    InvoiceRepository,
    SubscriptionLineRepository,
    TaxRepository,
)
from app.services.billing.discount_strategies import DiscountStrategyFactory


class InvoiceBuilder:
    """
    Fluent builder for Invoice creation.

    Each method returns ``self`` (or an awaitable returning ``self``)
    enabling a chained build pipeline.
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> None:
        self._db = db
        self._tenant_id = tenant_id
        self._subscription: Optional[Subscription] = None
        self._sub_lines: Sequence[SubscriptionLine] = []
        self._invoice_lines: list[dict] = []
        self._subtotal = Decimal("0.00")
        self._discount_total = Decimal("0.00")
        self._tax_total = Decimal("0.00")
        self._discount_id: Optional[uuid.UUID] = None
        self._invoice_number: Optional[str] = None

    def for_subscription(self, sub: Subscription) -> InvoiceBuilder:
        """Set the subscription to generate an invoice for."""
        self._subscription = sub
        return self

    async def add_lines(self) -> InvoiceBuilder:
        """Load subscription lines and build invoice lines."""
        if self._subscription is None:
            raise ValidationException(
                [{"field": "subscription", "message": "Subscription not set."}]
            )

        line_repo = SubscriptionLineRepository(
            self._db, self._tenant_id
        )
        self._sub_lines = await line_repo.find_by_subscription(
            self._subscription.id
        )

        for sl in self._sub_lines:
            line_total = (sl.unit_price * sl.qty).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            self._invoice_lines.append({
                "product_id": sl.product_id,
                "qty": sl.qty,
                "unit_price": sl.unit_price,
                "tax_id": sl.tax_ids[0] if sl.tax_ids else None,
                "discount_id": None,
            })
            self._subtotal += line_total

        return self

    async def apply_discount(
        self, discount_id: Optional[uuid.UUID]
    ) -> InvoiceBuilder:
        """Apply a discount (if any) to the subtotal."""
        if discount_id is None:
            return self

        repo = DiscountRepository(self._db, self._tenant_id)
        try:
            discount = await repo.find_by_id(discount_id)
        except NotFoundException:
            return self

        # Check usage limit
        if (
            discount.usage_limit is not None
            and discount.used_count >= discount.usage_limit
        ):
            raise ValidationException(
                [{"field": "discount", "message": "Discount has reached its usage limit."}],
                message="Discount has reached its usage limit.",
            )

        # Check date validity
        today = date.today()
        if not (discount.start_date <= today <= discount.end_date):
            return self

        # Check min purchase
        if self._subtotal < discount.min_purchase:
            return self

        strategy = DiscountStrategyFactory.create(discount.type)
        self._discount_total = strategy.apply(self._subtotal, discount)
        self._discount_id = discount_id

        # Increment usage
        discount.used_count += 1
        await self._db.flush()

        return self

    async def apply_tax(self) -> InvoiceBuilder:
        """Calculate tax across all invoice lines."""
        tax_repo = TaxRepository(self._db, self._tenant_id)

        for line_data in self._invoice_lines:
            if line_data["tax_id"] is None:
                continue
            try:
                tax = await tax_repo.find_by_id(line_data["tax_id"])
            except NotFoundException:
                continue

            line_amount = (
                Decimal(str(line_data["unit_price"])) * line_data["qty"]
            )
            tax_amount = (
                line_amount * tax.rate / Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self._tax_total += tax_amount

        return self

    async def build(self) -> Invoice:
        """Commit the invoice and its lines to the database."""
        if self._subscription is None:
            raise ValidationException(
                [{"field": "subscription", "message": "Subscription not set."}]
            )

        inv_repo = InvoiceRepository(self._db, self._tenant_id)
        self._invoice_number = await inv_repo.next_number()

        total = (
            self._subtotal - self._discount_total + self._tax_total
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Due date: 30 days from now (follows payment_terms pattern)
        due_date = date.today() + timedelta(days=30)

        invoice = await inv_repo.create({
            "invoice_number": self._invoice_number,
            "subscription_id": self._subscription.id,
            "customer_id": self._subscription.customer_id,
            "discount_id": self._discount_id,
            "status": InvoiceStatus.DRAFT,
            "due_date": due_date,
            "subtotal": self._subtotal,
            "tax_total": self._tax_total,
            "discount_total": self._discount_total,
            "total": total,
            "amount_paid": Decimal("0.00"),
        })

        # Create invoice line items
        for line_data in self._invoice_lines:
            line = InvoiceLine(
                tenant_id=self._tenant_id,
                invoice_id=invoice.id,
                **line_data,
            )
            self._db.add(line)

        await self._db.flush()
        await self._db.refresh(invoice)

        return invoice
