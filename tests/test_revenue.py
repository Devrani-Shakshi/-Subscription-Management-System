"""
Tests for revenue recognition module.

Covers:
  - Ratable recognition: splits evenly across periods
  - Milestone recognition: single immediate recognition
  - UPSERT idempotency: re-processing replaces rows
  - Timeline aggregation
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus
from app.services.revenue.service import RevenueRecognitionService
from app.services.revenue.strategies import (
    MilestoneRecognitionStrategy,
    RatableRecognitionStrategy,
)


# ═══════════════════════════════════════════════════════════════
# Strategy tests (pure, no DB)
# ═══════════════════════════════════════════════════════════════


class FakeInvoice:
    """Lightweight invoice stub for strategy tests."""

    def __init__(self, total: Decimal, due_date: date):
        self.total = total
        self.due_date = due_date


class TestRatableRecognition:
    """Test RatableRecognitionStrategy."""

    def test_splits_evenly_over_12_months(self):
        strategy = RatableRecognitionStrategy()
        invoice = FakeInvoice(
            total=Decimal("1200.00"), due_date=date(2026, 1, 1)
        )
        rows = strategy.recognize(invoice)
        assert len(rows) == 12

        # All amounts should sum to total
        total = sum(r.recognized_amount for r in rows)
        assert total == Decimal("1200.00")

        # Each month should be ~$100
        for row in rows[:-1]:
            assert row.recognized_amount == Decimal("100.00")

    def test_zero_invoice_produces_no_rows(self):
        strategy = RatableRecognitionStrategy()
        invoice = FakeInvoice(
            total=Decimal("0"), due_date=date(2026, 1, 1)
        )
        rows = strategy.recognize(invoice)
        assert len(rows) == 0

    def test_rounding_handled_correctly(self):
        """$100 / 12 months = rounding handled in last month."""
        strategy = RatableRecognitionStrategy()
        invoice = FakeInvoice(
            total=Decimal("100.00"), due_date=date(2026, 1, 1)
        )
        rows = strategy.recognize(invoice)
        total = sum(r.recognized_amount for r in rows)
        assert total == Decimal("100.00")


class TestMilestoneRecognition:
    """Test MilestoneRecognitionStrategy."""

    def test_full_amount_on_due_date(self):
        strategy = MilestoneRecognitionStrategy()
        invoice = FakeInvoice(
            total=Decimal("500.00"), due_date=date(2026, 6, 15)
        )
        rows = strategy.recognize(invoice)
        assert len(rows) == 1
        assert rows[0].recognized_amount == Decimal("500.00")
        assert rows[0].recognition_date == date(2026, 6, 15)
        assert rows[0].period == "2026-06"

    def test_zero_invoice_produces_no_rows(self):
        strategy = MilestoneRecognitionStrategy()
        invoice = FakeInvoice(
            total=Decimal("0"), due_date=date(2026, 1, 1)
        )
        rows = strategy.recognize(invoice)
        assert len(rows) == 0


# ═══════════════════════════════════════════════════════════════
# Service tests (DB-backed)
# ═══════════════════════════════════════════════════════════════


class TestRevenueRecognitionService:
    """Test RevenueRecognitionService DB operations."""

    @pytest.mark.asyncio
    async def test_process_creates_rows(
        self, db: AsyncSession, tenant, confirmed_invoice
    ):
        """Processing a confirmed invoice creates recognition rows."""
        svc = RevenueRecognitionService(db, tenant.id)
        count = await svc.process(confirmed_invoice.id)
        assert count == 12  # Default ratable: 12 months

    @pytest.mark.asyncio
    async def test_process_idempotent(
        self, db: AsyncSession, tenant, confirmed_invoice
    ):
        """Re-processing same invoice replaces rows (no duplicates)."""
        svc = RevenueRecognitionService(db, tenant.id)

        count1 = await svc.process(confirmed_invoice.id)
        count2 = await svc.process(confirmed_invoice.id)

        assert count1 == count2  # Same number

    @pytest.mark.asyncio
    async def test_milestone_strategy(
        self, db: AsyncSession, tenant, confirmed_invoice
    ):
        """Using milestone strategy creates single row."""
        svc = RevenueRecognitionService(
            db, tenant.id,
            strategy=MilestoneRecognitionStrategy(),
        )
        count = await svc.process(confirmed_invoice.id)
        assert count == 1

    @pytest.mark.asyncio
    async def test_nonexistent_invoice_returns_zero(
        self, db: AsyncSession, tenant
    ):
        """Processing unknown invoice → 0 rows."""
        svc = RevenueRecognitionService(db, tenant.id)
        count = await svc.process(uuid.uuid4())
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_timeline(
        self, db: AsyncSession, tenant, confirmed_invoice
    ):
        """get_timeline returns aggregated data after processing."""
        svc = RevenueRecognitionService(db, tenant.id)
        await svc.process(confirmed_invoice.id)

        timeline = await svc.get_timeline()
        assert len(timeline) > 0
        assert "month" in timeline[0]
        assert "recognized" in timeline[0]
        assert "cumulative" in timeline[0]
