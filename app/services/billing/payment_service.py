"""
Payment Service — business logic for recording and processing payments.

Responsibilities:
- Record company-side manual payments
- Process portal customer payments
- Payment validation (amount ≤ outstanding)
- Auto-mark invoice as paid when fully paid
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus, PaymentMethod
from app.exceptions.base import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.repositories.billing import InvoiceRepository, PaymentRepository
from app.services.base import BaseService


class PaymentService(BaseService):
    """All payment business rules. Routers only call this."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> None:
        super().__init__(db)
        self._tenant_id = tenant_id
        self._repo = PaymentRepository(db, tenant_id)
        self._inv_repo = InvoiceRepository(db, tenant_id)

    # ── Record payment (company) ─────────────────────────────────

    async def record_payment(
        self,
        invoice_id: uuid.UUID,
        amount: Decimal,
        method: PaymentMethod,
        paid_at: datetime | None = None,
    ) -> Payment:
        """Record a manual payment against an invoice."""
        invoice = await self._inv_repo.find_by_id(invoice_id)
        self._validate_payment(invoice, amount)

        payment = await self._repo.create({
            "invoice_id": invoice_id,
            "customer_id": invoice.customer_id,
            "method": method,
            "amount": amount,
            "paid_at": paid_at or datetime.utcnow(),
        })

        await self._update_invoice_paid(invoice, amount)
        return payment

    # ── Portal pay ───────────────────────────────────────────────

    async def portal_pay(
        self,
        invoice_id: uuid.UUID,
        customer_id: uuid.UUID,
        method: PaymentMethod = PaymentMethod.CARD,
    ) -> Payment:
        """
        Portal customer pays full outstanding amount.

        In production this would integrate with Stripe.
        """
        inv = await self._inv_repo.find_by_id(invoice_id)

        # Ownership check
        if inv.customer_id != customer_id:
            raise NotFoundException("Invoice not found.")

        if inv.status == InvoiceStatus.PAID:
            raise ConflictException("Invoice is already paid.")

        if inv.status not in (
            InvoiceStatus.CONFIRMED,
            InvoiceStatus.OVERDUE,
        ):
            raise ConflictException(
                "Only confirmed or overdue invoices can be paid."
            )

        amount = inv.amount_due

        payment = await self._repo.create({
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "method": method,
            "amount": amount,
            "paid_at": datetime.utcnow(),
        })

        await self._update_invoice_paid(inv, amount)
        return payment

    # ── List ─────────────────────────────────────────────────────

    async def list_payments(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Payment], int]:
        """List all payments for the tenant."""
        payments = await self._repo.find_all(
            offset=offset, limit=limit
        )
        total = await self._repo.count()
        return list(payments), total

    async def list_by_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> list[Payment]:
        """List payments for a specific invoice."""
        return list(await self._repo.find_by_invoice(invoice_id))

    # ── Internal ─────────────────────────────────────────────────

    def _validate_payment(
        self,
        invoice: Invoice,
        amount: Decimal,
    ) -> None:
        """Business rule checks before accepting payment."""
        if invoice.status == InvoiceStatus.CANCELLED:
            raise ConflictException(
                "Cannot pay a cancelled invoice."
            )
        if invoice.status == InvoiceStatus.PAID:
            raise ConflictException(
                "Invoice is already paid."
            )
        if invoice.status == InvoiceStatus.DRAFT:
            raise ConflictException(
                "Invoice must be confirmed before payment."
            )

        outstanding = invoice.amount_due
        if amount > outstanding:
            raise ValidationException([{
                "field": "amount",
                "message": (
                    f"Amount (${amount}) exceeds balance (${outstanding})."
                ),
            }])

    async def _update_invoice_paid(
        self,
        invoice: Invoice,
        amount: Decimal,
    ) -> None:
        """Update invoice amount_paid and status."""
        new_paid = invoice.amount_paid + amount
        update_data: dict = {"amount_paid": new_paid}

        if new_paid >= invoice.total:
            update_data["status"] = InvoiceStatus.PAID

        await self._inv_repo.update(invoice.id, update_data)
