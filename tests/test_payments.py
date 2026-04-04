"""
Tests for payment recording, validation, and invoice auto-marking.

Covers:
- Recording manual payments (company)
- Portal customer payments
- Amount exceeds balance validation
- Paying cancelled/draft invoice rejection
- Auto-marking invoice as paid
- Payment listing
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus, PaymentMethod
from app.exceptions.base import ConflictException, NotFoundException, ValidationException
from app.services.billing.payment_service import PaymentService


# ═══════════════════════════════════════════════════════════════
# Payment Recording Tests (Company)
# ═══════════════════════════════════════════════════════════════


class TestPaymentRecording:
    """Test company-side manual payment recording."""

    @pytest.mark.asyncio
    async def test_record_payment_success(
        self, db, tenant, confirmed_invoice
    ):
        """Record a valid payment against a confirmed invoice."""
        svc = PaymentService(db, tenant.id)
        payment = await svc.record_payment(
            invoice_id=confirmed_invoice.id,
            amount=Decimal("50.00"),
            method=PaymentMethod.CARD,
        )

        assert payment.amount == Decimal("50.00")
        assert payment.method == PaymentMethod.CARD
        assert payment.invoice_id == confirmed_invoice.id
        assert payment.customer_id == confirmed_invoice.customer_id

    @pytest.mark.asyncio
    async def test_record_payment_full_marks_paid(
        self, db, tenant, confirmed_invoice
    ):
        """Paying full amount auto-marks invoice as PAID."""
        svc = PaymentService(db, tenant.id)
        await svc.record_payment(
            invoice_id=confirmed_invoice.id,
            amount=confirmed_invoice.total,
            method=PaymentMethod.BANK,
        )

        # Refresh to get updated status
        from app.repositories.billing import InvoiceRepository
        repo = InvoiceRepository(db, tenant.id)
        inv = await repo.find_by_id(confirmed_invoice.id)
        assert inv.status == InvoiceStatus.PAID

    @pytest.mark.asyncio
    async def test_record_payment_exceeds_balance(
        self, db, tenant, confirmed_invoice
    ):
        """Payment exceeding outstanding balance raises ValidationException."""
        svc = PaymentService(db, tenant.id)
        with pytest.raises(ValidationException):
            await svc.record_payment(
                invoice_id=confirmed_invoice.id,
                amount=Decimal("999.99"),
                method=PaymentMethod.CARD,
            )

    @pytest.mark.asyncio
    async def test_record_payment_draft_invoice_rejected(
        self, db, tenant, invoice
    ):
        """Cannot pay a draft invoice."""
        svc = PaymentService(db, tenant.id)
        with pytest.raises(ConflictException, match="confirmed"):
            await svc.record_payment(
                invoice_id=invoice.id,
                amount=Decimal("10.00"),
                method=PaymentMethod.CARD,
            )

    @pytest.mark.asyncio
    async def test_record_payment_cancelled_invoice_rejected(
        self, db, tenant, invoice
    ):
        """Cannot pay a cancelled invoice."""
        invoice.status = InvoiceStatus.CANCELLED
        await db.flush()

        svc = PaymentService(db, tenant.id)
        with pytest.raises(ConflictException, match="cancelled"):
            await svc.record_payment(
                invoice_id=invoice.id,
                amount=Decimal("10.00"),
                method=PaymentMethod.CARD,
            )

    @pytest.mark.asyncio
    async def test_record_payment_with_custom_date(
        self, db, tenant, confirmed_invoice
    ):
        """Payment can specify a custom paid_at date."""
        custom_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
        svc = PaymentService(db, tenant.id)
        payment = await svc.record_payment(
            invoice_id=confirmed_invoice.id,
            amount=Decimal("10.00"),
            method=PaymentMethod.CASH,
            paid_at=custom_date,
        )
        assert payment.paid_at.year == 2026
        assert payment.paid_at.month == 1
        assert payment.paid_at.day == 15


# ═══════════════════════════════════════════════════════════════
# Portal Payment Tests
# ═══════════════════════════════════════════════════════════════


class TestPortalPayment:
    """Test portal customer self-service payment."""

    @pytest.mark.asyncio
    async def test_portal_pay_success(
        self, db, tenant, confirmed_invoice, portal_user
    ):
        """Portal user pays full outstanding amount."""
        svc = PaymentService(db, tenant.id)
        payment = await svc.portal_pay(
            invoice_id=confirmed_invoice.id,
            customer_id=portal_user.id,
        )

        assert payment.amount == confirmed_invoice.total
        assert payment.method == PaymentMethod.CARD

    @pytest.mark.asyncio
    async def test_portal_pay_wrong_customer(
        self, db, tenant, confirmed_invoice
    ):
        """Portal payment for wrong customer raises NotFoundException."""
        svc = PaymentService(db, tenant.id)
        with pytest.raises(NotFoundException):
            await svc.portal_pay(
                invoice_id=confirmed_invoice.id,
                customer_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_portal_pay_already_paid(
        self, db, tenant, confirmed_invoice, portal_user
    ):
        """Cannot pay an already paid invoice."""
        confirmed_invoice.status = InvoiceStatus.PAID
        await db.flush()

        svc = PaymentService(db, tenant.id)
        with pytest.raises(ConflictException, match="already paid"):
            await svc.portal_pay(
                invoice_id=confirmed_invoice.id,
                customer_id=portal_user.id,
            )

    @pytest.mark.asyncio
    async def test_portal_pay_draft_rejected(
        self, db, tenant, invoice, portal_user
    ):
        """Cannot pay a draft invoice through portal."""
        svc = PaymentService(db, tenant.id)
        with pytest.raises(ConflictException, match="confirmed or overdue"):
            await svc.portal_pay(
                invoice_id=invoice.id,
                customer_id=portal_user.id,
            )


# ═══════════════════════════════════════════════════════════════
# Payment Listing Tests
# ═══════════════════════════════════════════════════════════════


class TestPaymentListing:
    """Test payment listing and querying."""

    @pytest.mark.asyncio
    async def test_list_payments(
        self, db, tenant, confirmed_invoice
    ):
        """List payments returns results after recording."""
        svc = PaymentService(db, tenant.id)
        await svc.record_payment(
            invoice_id=confirmed_invoice.id,
            amount=Decimal("25.00"),
            method=PaymentMethod.CARD,
        )

        payments, total = await svc.list_payments()
        assert total >= 1
        assert any(p.amount == Decimal("25.00") for p in payments)

    @pytest.mark.asyncio
    async def test_list_by_invoice(
        self, db, tenant, confirmed_invoice
    ):
        """List payments filtered by invoice."""
        svc = PaymentService(db, tenant.id)
        await svc.record_payment(
            invoice_id=confirmed_invoice.id,
            amount=Decimal("10.00"),
            method=PaymentMethod.CARD,
        )

        payments = await svc.list_by_invoice(confirmed_invoice.id)
        assert len(payments) >= 1
        assert all(p.invoice_id == confirmed_invoice.id for p in payments)
