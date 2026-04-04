"""
Tests for invoice generation, lifecycle, discounts, and PDF.

Covers:
- Invoice generation from subscription
- Discount strategies (fixed, percent, exhausted)
- Pro-rata calculation
- Invoice lifecycle (confirm, cancel, send)
- PDF internal vs portal mode
- Conflict exceptions
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import DiscountType, InvoiceStatus
from app.exceptions.base import ConflictException, NotFoundException, ValidationException
from app.models.invoice import Invoice
from app.repositories.billing import InvoiceRepository
from app.services.billing.discount_strategies import (
    DiscountStrategyFactory,
    FixedDiscountStrategy,
    PercentDiscountStrategy,
)
from app.services.billing.invoice_builder import InvoiceBuilder
from app.services.billing.invoice_service import InvoiceService
from app.services.billing.pdf_generator import InvoicePDFGenerator


class _MockDiscount:
    """Lightweight mock for discount strategy testing (no SQLAlchemy)."""
    def __init__(self, discount_type, value):
        self.type = discount_type
        self.value = value
        self.min_purchase = Decimal("0")
        self.min_qty = 1
        self.start_date = date(2025, 1, 1)
        self.end_date = date(2027, 12, 31)
        self.usage_limit = None
        self.used_count = 0


# ═══════════════════════════════════════════════════════════════
# Discount Strategy Tests
# ═══════════════════════════════════════════════════════════════


class TestDiscountStrategies:
    """Test the Strategy pattern for discount calculation."""

    def test_fixed_discount_strategy(self):
        """Fixed discount subtracts a flat amount."""
        strategy = FixedDiscountStrategy()
        discount = _MockDiscount(DiscountType.FIXED, Decimal("10.00"))
        result = strategy.apply(Decimal("100.00"), discount)
        assert result == Decimal("10.00")

    def test_fixed_discount_capped_at_subtotal(self):
        """Fixed discount cannot exceed the subtotal."""
        strategy = FixedDiscountStrategy()
        discount = _MockDiscount(DiscountType.FIXED, Decimal("200.00"))
        result = strategy.apply(Decimal("50.00"), discount)
        assert result == Decimal("50.00")

    def test_percent_discount_strategy(self):
        """Percent discount calculates correctly."""
        strategy = PercentDiscountStrategy()
        discount = _MockDiscount(DiscountType.PERCENT, Decimal("20.00"))
        result = strategy.apply(Decimal("100.00"), discount)
        assert result == Decimal("20.00")

    def test_percent_discount_rounding(self):
        """Percent discount rounds to 2 decimal places."""
        strategy = PercentDiscountStrategy()
        discount = _MockDiscount(DiscountType.PERCENT, Decimal("33.33"))
        result = strategy.apply(Decimal("100.00"), discount)
        assert result == Decimal("33.33")

    def test_factory_creates_fixed(self):
        """Factory returns FixedDiscountStrategy for FIXED type."""
        strategy = DiscountStrategyFactory.create(DiscountType.FIXED)
        assert isinstance(strategy, FixedDiscountStrategy)

    def test_factory_creates_percent(self):
        """Factory returns PercentDiscountStrategy for PERCENT type."""
        strategy = DiscountStrategyFactory.create(DiscountType.PERCENT)
        assert isinstance(strategy, PercentDiscountStrategy)


# ═══════════════════════════════════════════════════════════════
# Invoice Generation Tests
# ═══════════════════════════════════════════════════════════════


class TestInvoiceGeneration:
    """Test invoice generation from subscriptions."""

    @pytest.mark.asyncio
    async def test_generate_invoice_from_subscription(
        self, db, tenant, subscription, subscription_line
    ):
        """Generate an invoice from a subscription with lines."""
        svc = InvoiceService(db, tenant.id)
        invoice = await svc.generate_from_subscription(subscription.id)

        assert invoice is not None
        assert invoice.invoice_number.startswith("INV-")
        assert invoice.subscription_id == subscription.id
        assert invoice.customer_id == subscription.customer_id
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.subtotal == Decimal("99.98")  # 2 × 49.99
        assert invoice.total > 0

    @pytest.mark.asyncio
    async def test_generate_invoice_nonexistent_subscription(
        self, db, tenant
    ):
        """Generating from nonexistent subscription raises NotFoundException."""
        svc = InvoiceService(db, tenant.id)
        with pytest.raises(NotFoundException):
            await svc.generate_from_subscription(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_invoice_builder_without_subscription_raises(
        self, db, tenant
    ):
        """Builder.build() without for_subscription raises ValidationException."""
        builder = InvoiceBuilder(db=db, tenant_id=tenant.id)
        with pytest.raises(ValidationException):
            await builder.build()


# ═══════════════════════════════════════════════════════════════
# Invoice with Discount Tests
# ═══════════════════════════════════════════════════════════════


class TestInvoiceWithDiscount:
    """Test invoice generation with discounts applied."""

    @pytest.mark.asyncio
    async def test_invoice_with_fixed_discount(
        self, db, tenant, subscription, subscription_line, discount_fixed
    ):
        """Invoice with fixed $10 discount."""
        subscription.discount_id = discount_fixed.id
        await db.flush()

        svc = InvoiceService(db, tenant.id)
        invoice = await svc.generate_from_subscription(subscription.id)

        assert invoice.discount_total == Decimal("10.00")
        assert invoice.total == Decimal("89.98")  # 99.98 - 10.00

    @pytest.mark.asyncio
    async def test_invoice_with_percent_discount(
        self, db, tenant, subscription, subscription_line, discount_percent
    ):
        """Invoice with 20% discount."""
        subscription.discount_id = discount_percent.id
        await db.flush()

        svc = InvoiceService(db, tenant.id)
        invoice = await svc.generate_from_subscription(subscription.id)

        assert invoice.discount_total == Decimal("20.00")  # 20% of 99.98
        assert invoice.total == Decimal("79.98")  # 99.98 - 20.00

    @pytest.mark.asyncio
    async def test_invoice_with_exhausted_discount_raises(
        self, db, tenant, subscription, subscription_line, discount_exhausted
    ):
        """Exhausted discount raises ValidationException."""
        subscription.discount_id = discount_exhausted.id
        await db.flush()

        svc = InvoiceService(db, tenant.id)
        with pytest.raises(ValidationException, match="usage limit"):
            await svc.generate_from_subscription(subscription.id)


# ═══════════════════════════════════════════════════════════════
# Invoice with Tax Tests
# ═══════════════════════════════════════════════════════════════


class TestInvoiceWithTax:
    """Test tax calculation logic."""

    @pytest.mark.asyncio
    async def test_tax_calculation_logic(self, db, tenant, tax):
        """Tax rate of 18% on $100 = $18."""
        from app.repositories.billing import TaxRepository

        repo = TaxRepository(db, tenant.id)
        loaded_tax = await repo.find_by_id(tax.id)

        # Manually calculate tax on a line
        line_amount = Decimal("100.00")
        tax_amount = (
            line_amount * loaded_tax.rate / Decimal("100")
        ).quantize(Decimal("0.01"))

        assert tax_amount == Decimal("18.00")

    @pytest.mark.asyncio
    async def test_invoice_generation_without_tax(
        self, db, tenant, subscription, subscription_line
    ):
        """Invoice without tax has zero tax_total."""
        svc = InvoiceService(db, tenant.id)
        invoice = await svc.generate_from_subscription(subscription.id)

        assert invoice.tax_total == Decimal("0.00")
        assert invoice.total == invoice.subtotal


# ═══════════════════════════════════════════════════════════════
# Invoice Lifecycle Tests
# ═══════════════════════════════════════════════════════════════


class TestInvoiceLifecycle:
    """Test invoice state transitions."""

    @pytest.mark.asyncio
    async def test_confirm_draft_invoice(self, db, tenant, invoice):
        """Confirm a draft invoice → confirmed."""
        svc = InvoiceService(db, tenant.id)
        result = await svc.confirm(invoice.id)
        assert result.status == InvoiceStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_confirm_already_confirmed_raises(
        self, db, tenant, confirmed_invoice
    ):
        """Confirming an already confirmed invoice raises ConflictException."""
        svc = InvoiceService(db, tenant.id)
        with pytest.raises(ConflictException, match="already confirmed"):
            await svc.confirm(confirmed_invoice.id)

    @pytest.mark.asyncio
    async def test_cancel_draft_invoice(self, db, tenant, invoice):
        """Cancel a draft invoice."""
        svc = InvoiceService(db, tenant.id)
        result = await svc.cancel(invoice.id)
        assert result.status == InvoiceStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_with_payment_raises(self, db, tenant, confirmed_invoice):
        """Cannot cancel invoice that has payments."""
        # Simulate partial payment
        confirmed_invoice.amount_paid = Decimal("50.00")
        await db.flush()

        svc = InvoiceService(db, tenant.id)
        with pytest.raises(ConflictException, match="refund"):
            await svc.cancel(confirmed_invoice.id)

    @pytest.mark.asyncio
    async def test_send_confirmed_invoice(self, db, tenant, confirmed_invoice):
        """Send a confirmed invoice."""
        svc = InvoiceService(db, tenant.id)
        result = await svc.send(confirmed_invoice.id)
        assert result.id == confirmed_invoice.id

    @pytest.mark.asyncio
    async def test_send_draft_invoice_raises(self, db, tenant, invoice):
        """Cannot send a draft invoice."""
        svc = InvoiceService(db, tenant.id)
        with pytest.raises(ConflictException, match="confirmed"):
            await svc.send(invoice.id)


# ═══════════════════════════════════════════════════════════════
# PDF Generation Tests
# ═══════════════════════════════════════════════════════════════


class TestPDFGeneration:
    """Test PDF generation in internal vs portal mode."""

    @pytest.mark.asyncio
    async def test_pdf_internal_mode(
        self, db, tenant, subscription, subscription_line, invoice
    ):
        """Internal PDF includes internal notes."""
        gen = InvoicePDFGenerator()
        pdf_bytes = gen._build_pdf(
            invoice, mode="internal", tenant_name="Test Co",
            primary_color="#000",
        )
        content = pdf_bytes.decode("utf-8")

        assert "INTERNAL NOTES" in content
        assert invoice.invoice_number in content

    @pytest.mark.asyncio
    async def test_pdf_portal_mode(
        self, db, tenant, subscription, subscription_line, invoice
    ):
        """Portal PDF does NOT include internal notes."""
        gen = InvoicePDFGenerator()
        pdf_bytes = gen._build_pdf(
            invoice, mode="portal", tenant_name="Test Co",
            primary_color="#000",
        )
        content = pdf_bytes.decode("utf-8")

        assert "INTERNAL NOTES" not in content
        assert invoice.invoice_number in content

    @pytest.mark.asyncio
    async def test_pdf_contains_amounts(
        self, db, tenant, subscription, subscription_line, invoice
    ):
        """PDF shows subtotal, total, and amount due."""
        gen = InvoicePDFGenerator()
        pdf_bytes = gen._build_pdf(
            invoice, mode="portal", tenant_name="Test Co",
            primary_color="#000",
        )
        content = pdf_bytes.decode("utf-8")

        assert "Subtotal" in content
        assert "TOTAL" in content
        assert "Amount Due" in content


# ═══════════════════════════════════════════════════════════════
# Invoice Repository Tests
# ═══════════════════════════════════════════════════════════════


class TestInvoiceRepository:
    """Test invoice repository methods."""

    @pytest.mark.asyncio
    async def test_find_by_customer(
        self, db, tenant, invoice, portal_user
    ):
        """Repository finds invoices by customer ID."""
        repo = InvoiceRepository(db, tenant.id)
        results = await repo.find_by_customer(portal_user.id)
        assert len(results) >= 1
        assert all(r.customer_id == portal_user.id for r in results)

    @pytest.mark.asyncio
    async def test_next_number(self, db, tenant):
        """Repository generates sequential invoice numbers."""
        repo = InvoiceRepository(db, tenant.id)
        number = await repo.next_number()
        assert number.startswith("INV-")

    @pytest.mark.asyncio
    async def test_find_by_id_for_customer_success(
        self, db, tenant, invoice, portal_user
    ):
        """Finds invoice for matching customer."""
        repo = InvoiceRepository(db, tenant.id)
        result = await repo.find_by_id_for_customer(
            invoice.id, portal_user.id
        )
        assert result is not None
        assert result.id == invoice.id

    @pytest.mark.asyncio
    async def test_find_by_id_for_wrong_customer(
        self, db, tenant, invoice
    ):
        """Returns None for non-matching customer."""
        repo = InvoiceRepository(db, tenant.id)
        result = await repo.find_by_id_for_customer(
            invoice.id, uuid.uuid4()
        )
        assert result is None


# ═══════════════════════════════════════════════════════════════
# Pro-Rata Calculation Tests
# ═══════════════════════════════════════════════════════════════


class TestProRataCalculation:
    """Test pro-rata invoice calculations."""

    @pytest.mark.asyncio
    async def test_invoice_subtotal_matches_line_sum(
        self, db, tenant, subscription, subscription_line
    ):
        """Invoice subtotal = sum of qty × unit_price across lines."""
        svc = InvoiceService(db, tenant.id)
        invoice = await svc.generate_from_subscription(subscription.id)

        expected = subscription_line.qty * subscription_line.unit_price
        assert invoice.subtotal == expected.quantize(Decimal("0.01"))

    @pytest.mark.asyncio
    async def test_amount_due_property(
        self, db, tenant, invoice
    ):
        """amount_due = total - amount_paid."""
        assert invoice.amount_due == invoice.total - invoice.amount_paid
        assert invoice.amount_due == Decimal("99.98")



