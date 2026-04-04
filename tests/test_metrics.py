"""
Tests for health dashboard metrics module.

Covers:
  - MRR/ARR/NRR calculation correctness
  - ChurnRate calculation
  - LTV calculation
  - DashboardService aggregation
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.metrics.calculators import (
    ARRCalculator,
    ChurnRateCalculator,
    DateRange,
    LTVCalculator,
    MRRCalculator,
    NRRCalculator,
)
from app.services.metrics.dashboard import DashboardService


def _default_range() -> DateRange:
    return DateRange(
        start=date.today() - timedelta(days=30),
        end=date.today(),
    )


class TestMRRCalculator:
    """Test MRR calculation."""

    @pytest.mark.asyncio
    async def test_mrr_with_active_subscription(
        self, db: AsyncSession, tenant, subscription, plan
    ):
        """MRR = sum of active plan prices."""
        calc = MRRCalculator(db, tenant.id, _default_range())
        result = await calc.calculate()
        assert result.name == "MRR"
        assert result.raw_value > 0

    @pytest.mark.asyncio
    async def test_mrr_empty_tenant(self, db: AsyncSession, tenant):
        """MRR = 0 for tenant with no active subs."""
        # Use a fresh tenant with no subs
        new_tenant_id = uuid.uuid4()
        calc = MRRCalculator(db, new_tenant_id, _default_range())
        result = await calc.calculate()
        assert result.raw_value == Decimal("0")


class TestARRCalculator:
    """Test ARR = MRR × 12."""

    @pytest.mark.asyncio
    async def test_arr_is_12x_mrr(
        self, db: AsyncSession, tenant, subscription, plan
    ):
        calc = ARRCalculator(db, tenant.id, _default_range())
        result = await calc.calculate()
        assert result.name == "ARR"

        # Verify it's 12x MRR
        mrr_calc = MRRCalculator(db, tenant.id, _default_range())
        mrr = await mrr_calc.calculate()
        assert result.raw_value == mrr.raw_value * 12


class TestChurnRateCalculator:
    """Test churn rate calculation."""

    @pytest.mark.asyncio
    async def test_no_closed_subscriptions(
        self, db: AsyncSession, tenant, subscription
    ):
        """No closed subs → churn rate based on ratio."""
        calc = ChurnRateCalculator(db, tenant.id, _default_range())
        result = await calc.calculate()
        assert result.name == "Churn Rate"
        # With 1 active, 0 closed: rate = 0%
        assert result.raw_value == Decimal("0")


class TestNRRCalculator:
    """Test net revenue retention."""

    @pytest.mark.asyncio
    async def test_nrr_calculation(
        self, db: AsyncSession, tenant, subscription
    ):
        calc = NRRCalculator(db, tenant.id, _default_range())
        result = await calc.calculate()
        assert result.name == "NRR"
        assert "%" in result.value


class TestLTVCalculator:
    """Test customer lifetime value."""

    @pytest.mark.asyncio
    async def test_ltv_no_customers(self, db: AsyncSession, tenant):
        """LTV = 0 when no customers."""
        new_id = uuid.uuid4()
        calc = LTVCalculator(db, new_id, _default_range())
        result = await calc.calculate()
        assert result.name == "LTV"
        assert result.raw_value == Decimal("0")


class TestDashboardService:
    """Test DashboardService aggregation."""

    @pytest.mark.asyncio
    async def test_get_all_returns_all_metrics(
        self, db: AsyncSession, tenant, subscription, plan,
        portal_user,
    ):
        """get_all should return all 5 metric keys."""
        svc = DashboardService(db, tenant.id)
        results = await svc.get_all()

        assert "MRR" in results
        assert "ARR" in results
        assert "NRR" in results
        assert "Churn Rate" in results
        assert "LTV" in results

        for key, value in results.items():
            assert "value" in value
            assert "raw_value" in value
