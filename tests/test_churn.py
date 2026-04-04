"""
Tests for churn prediction module.

Covers:
  - Signal compute (each signal tested individually)
  - ChurnScoreEngine score capping at 100
  - ChurnService batch computation + UPSERT
  - Risk level classification
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    DunningAction,
    DunningStatus,
    InvoiceStatus,
    SubscriptionStatus,
    UserRole,
)
from app.services.churn.engine import ChurnScoreEngine
from app.services.churn.service import ChurnService, risk_level
from app.services.churn.signals import (
    ChurnSignal,
    DowngradeSignal,
    DunningSignal,
    LoginInactivitySignal,
    OverdueInvoiceSignal,
    PausedSignal,
    SignalResult,
)


# ═══════════════════════════════════════════════════════════════
# Signal compute tests
# ═══════════════════════════════════════════════════════════════


class TestLoginInactivitySignal:
    """Test LoginInactivitySignal."""

    @pytest.mark.asyncio
    async def test_no_login_history_triggers(
        self, db: AsyncSession, portal_user
    ):
        """No login session → signal triggered."""
        signal = LoginInactivitySignal()
        result = await signal.compute(portal_user, db)
        assert result.triggered is True
        assert result.weight == 20
        assert result.key == "login_inactivity"

    @pytest.mark.asyncio
    async def test_recent_login_does_not_trigger(
        self, db: AsyncSession, portal_user, tenant
    ):
        """Login within 14 days → not triggered."""
        from app.models.session import Session as SessionModel

        session = SessionModel(
            user_id=portal_user.id,
            tenant_id=tenant.id,
            refresh_token_hash="test",
            family_id=uuid.uuid4(),
            device_fingerprint="test",
            ip_subnet="127.0.0.0",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(session)
        await db.flush()

        signal = LoginInactivitySignal()
        result = await signal.compute(portal_user, db)
        assert result.triggered is False


class TestOverdueInvoiceSignal:
    """Test OverdueInvoiceSignal."""

    @pytest.mark.asyncio
    async def test_no_overdue_invoices(
        self, db: AsyncSession, portal_user
    ):
        """0 overdue invoices → not triggered (threshold is > 1)."""
        signal = OverdueInvoiceSignal()
        result = await signal.compute(portal_user, db)
        assert result.triggered is False

    @pytest.mark.asyncio
    async def test_multiple_overdue_triggers(
        self, db: AsyncSession, portal_user, tenant, subscription
    ):
        """2+ overdue invoices → triggered."""
        from app.models.invoice import Invoice

        for i in range(3):
            inv = Invoice(
                tenant_id=tenant.id,
                invoice_number=f"OD-{uuid.uuid4().hex[:6]}",
                subscription_id=subscription.id,
                customer_id=portal_user.id,
                status=InvoiceStatus.OVERDUE,
                due_date=date.today() - timedelta(days=30),
                subtotal=Decimal("100.00"),
                tax_total=Decimal("0"),
                discount_total=Decimal("0"),
                total=Decimal("100.00"),
                amount_paid=Decimal("0"),
            )
            db.add(inv)
        await db.flush()

        signal = OverdueInvoiceSignal()
        result = await signal.compute(portal_user, db)
        assert result.triggered is True
        assert result.weight == 30


class TestPausedSignal:
    """Test PausedSignal."""

    @pytest.mark.asyncio
    async def test_paused_subscription_triggers(
        self, db: AsyncSession, portal_user, tenant, plan
    ):
        """Paused subscription → triggered."""
        from app.models.subscription import Subscription

        sub = Subscription(
            tenant_id=tenant.id,
            number=f"PAUSE-{uuid.uuid4().hex[:6]}",
            customer_id=portal_user.id,
            plan_id=plan.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status=SubscriptionStatus.PAUSED,
        )
        db.add(sub)
        await db.flush()

        signal = PausedSignal()
        result = await signal.compute(portal_user, db)
        assert result.triggered is True
        assert result.weight == 40


# ═══════════════════════════════════════════════════════════════
# Engine tests
# ═══════════════════════════════════════════════════════════════


class TestChurnScoreEngine:
    """Test ChurnScoreEngine aggregate scoring."""

    @pytest.mark.asyncio
    async def test_score_capping_at_100(
        self, db: AsyncSession, portal_user
    ):
        """Score should never exceed 100."""

        class AlwaysTriggered(ChurnSignal):
            async def compute(self, customer, db) -> SignalResult:
                return SignalResult(
                    key="test", weight=60, triggered=True
                )

        engine = ChurnScoreEngine(
            signals=[AlwaysTriggered(), AlwaysTriggered()]
        )
        score, breakdown = await engine.score(portal_user, db)
        assert score == 100  # 60+60=120 capped to 100

    @pytest.mark.asyncio
    async def test_no_triggered_signals(
        self, db: AsyncSession, portal_user
    ):
        """No triggered signals → score 0."""

        class NeverTriggered(ChurnSignal):
            async def compute(self, customer, db) -> SignalResult:
                return SignalResult(
                    key="test", weight=50, triggered=False
                )

        engine = ChurnScoreEngine(signals=[NeverTriggered()])
        score, breakdown = await engine.score(portal_user, db)
        assert score == 0

    @pytest.mark.asyncio
    async def test_failing_signal_does_not_crash(
        self, db: AsyncSession, portal_user
    ):
        """A failing signal is logged but doesn't crash the engine."""

        class FailingSignal(ChurnSignal):
            async def compute(self, customer, db) -> SignalResult:
                raise RuntimeError("Signal broken!")

        class WorkingSignal(ChurnSignal):
            async def compute(self, customer, db) -> SignalResult:
                return SignalResult(
                    key="ok", weight=20, triggered=True
                )

        engine = ChurnScoreEngine(
            signals=[FailingSignal(), WorkingSignal()]
        )
        score, breakdown = await engine.score(portal_user, db)
        assert score == 20
        assert len(breakdown) == 2


# ═══════════════════════════════════════════════════════════════
# Service + risk level tests
# ═══════════════════════════════════════════════════════════════


class TestRiskLevel:
    """Test risk_level classification."""

    def test_low(self):
        from app.core.enums import ChurnRiskLevel
        assert risk_level(0) == ChurnRiskLevel.LOW
        assert risk_level(29) == ChurnRiskLevel.LOW

    def test_medium(self):
        from app.core.enums import ChurnRiskLevel
        assert risk_level(30) == ChurnRiskLevel.MEDIUM
        assert risk_level(69) == ChurnRiskLevel.MEDIUM

    def test_high(self):
        from app.core.enums import ChurnRiskLevel
        assert risk_level(70) == ChurnRiskLevel.HIGH
        assert risk_level(100) == ChurnRiskLevel.HIGH


class TestChurnService:
    """Test ChurnService batch operations."""

    @pytest.mark.asyncio
    async def test_compute_for_customer_upsert(
        self, db: AsyncSession, tenant, portal_user
    ):
        """compute_for_customer creates then updates (idempotent)."""
        svc = ChurnService(db, tenant.id)

        # First computation
        entry1 = await svc.compute_for_customer(portal_user)
        assert entry1.score >= 0

        # Second computation (UPSERT)
        entry2 = await svc.compute_for_customer(portal_user)
        assert entry2.id == entry1.id  # Same row updated

    @pytest.mark.asyncio
    async def test_compute_all_scores(
        self, db: AsyncSession, tenant, portal_user
    ):
        """compute_all_scores processes all portal_users."""
        svc = ChurnService(db, tenant.id)
        count = await svc.compute_all_scores()
        assert count >= 1

    @pytest.mark.asyncio
    async def test_list_churn_scores(
        self, db: AsyncSession, tenant, portal_user
    ):
        """list_churn_scores returns computed scores."""
        svc = ChurnService(db, tenant.id)
        await svc.compute_for_customer(portal_user)

        items, total = await svc.list_churn_scores()
        assert total >= 1
        assert items[0]["customer_id"] == portal_user.id
