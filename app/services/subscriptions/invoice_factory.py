"""
InvoiceFactory — Factory pattern for creating invoices.

Centralises all invoice creation logic so routers/services
never construct Invoice/InvoiceLine objects directly.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.subscription import Subscription
from app.models.subscription_line import SubscriptionLine
from app.services.subscriptions.pro_rata import ProRataResult


class InvoiceFactory:
    """Create invoices for various billing scenarios."""

    @classmethod
    async def create_from_subscription(
        cls,
        db: AsyncSession,
        sub: Subscription,
        tenant_id: uuid.UUID,
        *,
        payment_terms_days: int = 30,
    ) -> Invoice:
        """
        Generate a DRAFT invoice from all subscription lines.

        Used when activating a subscription for the first time.
        """
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id))
        count = result.scalar() or 0
        inv_number = f"INV-{count + 1:06d}"

        subtotal = Decimal("0.00")
        invoice = Invoice(
            tenant_id=tenant_id,
            invoice_number=inv_number,
            subscription_id=sub.id,
            customer_id=sub.customer_id,
            status=InvoiceStatus.DRAFT,
            due_date=date.today() + timedelta(days=payment_terms_days),
            subtotal=Decimal("0.00"),
            tax_total=Decimal("0.00"),
            discount_total=Decimal("0.00"),
            total=Decimal("0.00"),
        )
        db.add(invoice)
        await db.flush()
        await db.refresh(invoice)

        for line in sub.lines:
            line_total = line.unit_price * line.qty
            subtotal += line_total
            inv_line = InvoiceLine(
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                product_id=line.product_id,
                qty=line.qty,
                unit_price=line.unit_price,
            )
            db.add(inv_line)

        invoice.subtotal = subtotal
        invoice.total = subtotal  # tax/discount applied separately
        await db.flush()
        await db.refresh(invoice)
        return invoice

    @classmethod
    async def create_delta(
        cls,
        db: AsyncSession,
        sub: Subscription,
        pro_rata: ProRataResult,
        tenant_id: uuid.UUID,
    ) -> Invoice:
        """
        Generate a delta invoice for a mid-cycle plan upgrade.

        The amount_due from ProRataResult becomes the invoice total.
        """
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id))
        count = result.scalar() or 0
        inv_number = f"INV-{count + 1:06d}"

        invoice = Invoice(
            tenant_id=tenant_id,
            invoice_number=inv_number,
            subscription_id=sub.id,
            customer_id=sub.customer_id,
            status=InvoiceStatus.DRAFT,
            due_date=date.today() + timedelta(days=7),
            subtotal=pro_rata.amount_due,
            tax_total=Decimal("0.00"),
            discount_total=Decimal("0.00"),
            total=pro_rata.amount_due,
        )
        db.add(invoice)
        await db.flush()
        await db.refresh(invoice)
        return invoice
