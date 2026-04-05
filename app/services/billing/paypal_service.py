"""
PayPal Payment Service — business-logic layer bridging PayPal gateway
with the subscription/invoice system.

Responsibilities:
  - Create PayPal checkout for an invoice
  - Handle success callback (capture + record payment internally)
  - Handle failure callback (mark order as cancelled)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus, PaymentMethod, PayPalOrderStatus
from app.exceptions.base import (
    ConflictException,
    NotFoundException,
    ServiceException,
)
from app.models.invoice import Invoice
from app.repositories.billing import InvoiceRepository, PaymentRepository
from app.services.base import BaseService
from app.services.billing.paypal_gateway import PayPalGateway

logger = logging.getLogger(__name__)


class PayPalPaymentService(BaseService):
    """
    Orchestrates PayPal payment flow for invoices.

    Flow:
    1. create_checkout()    → creates PayPal order, returns approval URL
    2. handle_success()     → captures payment, records in DB, marks invoice paid
    3. handle_failure()     → marks order as cancelled/failed
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> None:
        super().__init__(db)
        self._tenant_id = tenant_id
        self._inv_repo = InvoiceRepository(db, tenant_id)
        self._pay_repo = PaymentRepository(db, tenant_id)
        self._gateway = PayPalGateway()

    # ── 1. Create Checkout ──────────────────────────────────────

    async def create_checkout(
        self,
        invoice_id: uuid.UUID,
        customer_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Creates a PayPal order for an invoice and returns the
        approval URL where the user should be redirected.

        Returns:
            {
                "paypal_order_id": "...",
                "approval_url": "https://www.paypal.com/...",
                "invoice_id": "...",
                "amount": "99.99",
                "status": "created",
            }
        """
        invoice = await self._inv_repo.find_by_id(invoice_id)

        # Ownership check (for portal users)
        if customer_id and invoice.customer_id != customer_id:
            raise NotFoundException("Invoice not found.")

        # Only confirmed/overdue invoices can be paid
        if invoice.status not in (
            InvoiceStatus.CONFIRMED,
            InvoiceStatus.OVERDUE,
        ):
            raise ConflictException(
                f"Cannot pay invoice in '{invoice.status.value}' status. "
                "Invoice must be confirmed first."
            )

        if invoice.status == InvoiceStatus.PAID:
            raise ConflictException("Invoice is already paid.")

        amount_due = invoice.amount_due
        if amount_due <= 0:
            raise ConflictException("No outstanding balance on this invoice.")

        # Create PayPal order
        result = await self._gateway.create_order(
            amount=str(amount_due),
            currency="USD",
            invoice_id=str(invoice_id),
            description=(
                f"Invoice #{invoice.invoice_number} - "
                f"Subscription Payment"
            ),
            custom_id=str(self._tenant_id),
        )

        logger.info(
            f"PayPal checkout created for invoice {invoice.invoice_number} | "
            f"Order: {result['order_id']} | Amount: {amount_due}"
        )

        return {
            "paypal_order_id": result["order_id"],
            "approval_url": result["approval_url"],
            "invoice_id": str(invoice_id),
            "amount": str(amount_due),
            "status": PayPalOrderStatus.CREATED.value,
        }

    # ── 2. Handle Success ───────────────────────────────────────

    async def handle_success(
        self,
        paypal_order_id: str,
        invoice_id: uuid.UUID,
        customer_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        SUCCESS callback — captures the PayPal payment and records
        it in the database. Marks the invoice as paid if fully paid.

        Called when PayPal redirects back to the success URL.

        Returns:
            {
                "status": "success",
                "paypal_order_id": "...",
                "capture_id": "...",
                "amount_paid": "99.99",
                "invoice_status": "paid",
                "payer_email": "buyer@example.com",
            }
        """
        # Capture payment on PayPal side
        capture_result = await self._gateway.capture_order(paypal_order_id)

        if capture_result["status"] != "COMPLETED":
            raise ServiceException(
                f"PayPal capture incomplete. Status: {capture_result['status']}"
            )

        # Load invoice
        invoice = await self._inv_repo.find_by_id(invoice_id)

        if customer_id and invoice.customer_id != customer_id:
            raise NotFoundException("Invoice not found.")

        amount = Decimal(capture_result["amount"])

        # Record payment in our DB
        payment = await self._pay_repo.create({
            "invoice_id": invoice_id,
            "customer_id": invoice.customer_id,
            "method": PaymentMethod.PAYPAL,
            "amount": amount,
            "paid_at": datetime.now(timezone.utc),
        })

        # Update invoice totals
        new_paid = invoice.amount_paid + amount
        update_data: dict = {"amount_paid": new_paid}

        if new_paid >= invoice.total:
            update_data["status"] = InvoiceStatus.PAID

        await self._inv_repo.update(invoice.id, update_data)

        logger.info(
            f"PayPal payment SUCCESS for invoice {invoice.invoice_number} | "
            f"Capture: {capture_result['capture_id']} | "
            f"Amount: {amount}"
        )

        return {
            "status": "success",
            "paypal_order_id": paypal_order_id,
            "capture_id": capture_result["capture_id"],
            "payment_id": str(payment.id),
            "amount_paid": str(amount),
            "invoice_status": update_data.get(
                "status", invoice.status
            ).value if hasattr(update_data.get("status", invoice.status), "value") else str(update_data.get("status", invoice.status)),
            "payer_email": capture_result.get("payer_email", ""),
        }

    # ── 3. Handle Failure ───────────────────────────────────────

    async def handle_failure(
        self,
        paypal_order_id: str,
        invoice_id: uuid.UUID,
        reason: str = "Payment cancelled or declined by user",
    ) -> dict[str, Any]:
        """
        FAILURE callback — handles payment cancellation or decline.

        Called when PayPal redirects to the cancel URL or
        the user declines the payment.

        Returns:
            {
                "status": "failed",
                "paypal_order_id": "...",
                "invoice_id": "...",
                "reason": "...",
            }
        """
        result = PayPalGateway.handle_failure(paypal_order_id, reason)

        logger.warning(
            f"PayPal payment FAILED for invoice {invoice_id} | "
            f"Order: {paypal_order_id} | Reason: {reason}"
        )

        return {
            "status": PayPalOrderStatus.FAILED.value,
            "paypal_order_id": paypal_order_id,
            "invoice_id": str(invoice_id),
            "reason": reason,
            "timestamp": result["timestamp"],
        }
