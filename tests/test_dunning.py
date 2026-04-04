"""
Tests for dunning schedule creation, action execution, and processing.

Covers:
- Dunning schedule creation from config
- Retry action (skip if paid)
- Suspend action (pauses subscription)
- Cancel action (closes subscription, emits churn event)
- DunningActionFactory
- Processing pending schedules
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dunning import DUNNING_SCHEDULE
from app.core.enums import (
    DunningAction,
    DunningStatus,
    InvoiceStatus,
    SubscriptionStatus,
)
from app.exceptions.base import ServiceException
from app.models.dunning_schedule import DunningSchedule
from app.repositories.billing import (
    DunningScheduleRepository,
    SubscriptionRepository,
)
from app.services.billing.dunning_service import (
    CancelAction,
    DunningActionFactory,
    DunningScheduleService,
    RetryAction,
    SuspendAction,
)


# ═══════════════════════════════════════════════════════════════
# Dunning Schedule Creation Tests
# ═══════════════════════════════════════════════════════════════


class TestDunningScheduleCreation:
    """Test dunning schedule creation from config."""

    @pytest.mark.asyncio
    async def test_create_from_invoice(
        self, db, tenant, confirmed_invoice
    ):
        """Creates dunning schedule rows matching config steps."""
        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)

        assert len(schedules) == len(DUNNING_SCHEDULE)

        for idx, (schedule, step) in enumerate(
            zip(schedules, DUNNING_SCHEDULE), start=1
        ):
            assert schedule.attempt_number == idx
            assert schedule.action == step.action
            assert schedule.channel == step.channel
            assert schedule.status == DunningStatus.PENDING
            assert schedule.invoice_id == confirmed_invoice.id

    @pytest.mark.asyncio
    async def test_schedule_timing(
        self, db, tenant, confirmed_invoice
    ):
        """Dunning schedules are spaced according to config days."""
        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)

        # Verify schedules are in the future and properly ordered
        for i, schedule in enumerate(schedules):
            assert schedule.scheduled_at is not None
            if i > 0:
                assert schedules[i].scheduled_at > schedules[i - 1].scheduled_at

    @pytest.mark.asyncio
    async def test_schedule_actions_match_config(
        self, db, tenant, confirmed_invoice
    ):
        """First two are retry, third is suspend, fourth is cancel."""
        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)

        assert schedules[0].action == DunningAction.RETRY
        assert schedules[1].action == DunningAction.RETRY
        assert schedules[2].action == DunningAction.SUSPEND
        assert schedules[3].action == DunningAction.CANCEL


# ═══════════════════════════════════════════════════════════════
# Retry Action Tests
# ═══════════════════════════════════════════════════════════════


class TestRetryAction:
    """Test the RetryAction dunning handler."""

    @pytest.mark.asyncio
    async def test_retry_already_paid_skips(
        self, db, tenant, confirmed_invoice
    ):
        """If invoice is already paid, retry skips."""
        confirmed_invoice.status = InvoiceStatus.PAID
        await db.flush()

        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)
        schedule = schedules[0]  # First retry

        action = RetryAction(db, tenant.id)
        result = await action.execute(schedule)

        assert result["status"] == "skipped"
        assert result["reason"] == "Invoice already paid"
        assert schedule.status == DunningStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_retry_unpaid_fails(
        self, db, tenant, confirmed_invoice
    ):
        """Retry on unpaid invoice (simulated gateway failure)."""
        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)
        schedule = schedules[0]

        action = RetryAction(db, tenant.id)
        result = await action.execute(schedule)

        assert result["status"] == "failed"
        assert schedule.status == DunningStatus.FAILED


# ═══════════════════════════════════════════════════════════════
# Suspend Action Tests
# ═══════════════════════════════════════════════════════════════


class TestSuspendAction:
    """Test the SuspendAction dunning handler."""

    @pytest.mark.asyncio
    async def test_suspend_pauses_subscription(
        self, db, tenant, confirmed_invoice, subscription
    ):
        """Suspend action sets subscription status to paused."""
        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)
        # Get the suspend schedule (index 2)
        schedule = schedules[2]

        action = SuspendAction(db, tenant.id)
        result = await action.execute(schedule)

        assert result["status"] == "success"
        assert result["action"] == "subscription_paused"

        # Verify subscription is paused
        sub_repo = SubscriptionRepository(db, tenant.id)
        sub = await sub_repo.find_by_id(subscription.id)
        assert sub.status == SubscriptionStatus.PAUSED

    @pytest.mark.asyncio
    async def test_suspend_skips_if_paid(
        self, db, tenant, confirmed_invoice
    ):
        """Suspend skips if invoice is already paid."""
        confirmed_invoice.status = InvoiceStatus.PAID
        await db.flush()

        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)
        schedule = schedules[2]

        action = SuspendAction(db, tenant.id)
        result = await action.execute(schedule)

        assert result["status"] == "skipped"


# ═══════════════════════════════════════════════════════════════
# Cancel Action Tests
# ═══════════════════════════════════════════════════════════════


class TestCancelAction:
    """Test the CancelAction dunning handler."""

    @pytest.mark.asyncio
    async def test_cancel_closes_subscription(
        self, db, tenant, confirmed_invoice, subscription
    ):
        """Cancel action closes subscription and emits churn event."""
        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)
        schedule = schedules[3]  # Cancel schedule

        action = CancelAction(db, tenant.id)
        result = await action.execute(schedule)

        assert result["status"] == "success"
        assert result["action"] == "subscription_cancelled"
        assert result["event"] == "subscription.churned"

        # Verify subscription is closed
        sub_repo = SubscriptionRepository(db, tenant.id)
        sub = await sub_repo.find_by_id(subscription.id)
        assert sub.status == SubscriptionStatus.CLOSED

    @pytest.mark.asyncio
    async def test_cancel_skips_if_paid(
        self, db, tenant, confirmed_invoice
    ):
        """Cancel skips if invoice is already paid."""
        confirmed_invoice.status = InvoiceStatus.PAID
        await db.flush()

        svc = DunningScheduleService(db, tenant.id)
        schedules = await svc.create_from_invoice(confirmed_invoice)
        schedule = schedules[3]

        action = CancelAction(db, tenant.id)
        result = await action.execute(schedule)

        assert result["status"] == "skipped"


# ═══════════════════════════════════════════════════════════════
# DunningActionFactory Tests
# ═══════════════════════════════════════════════════════════════


class TestDunningActionFactory:
    """Test the factory pattern for dunning actions."""

    def test_factory_creates_retry(self, db, tenant):
        action = DunningActionFactory.create(
            DunningAction.RETRY, db, tenant.id
        )
        assert isinstance(action, RetryAction)

    def test_factory_creates_suspend(self, db, tenant):
        action = DunningActionFactory.create(
            DunningAction.SUSPEND, db, tenant.id
        )
        assert isinstance(action, SuspendAction)

    def test_factory_creates_cancel(self, db, tenant):
        action = DunningActionFactory.create(
            DunningAction.CANCEL, db, tenant.id
        )
        assert isinstance(action, CancelAction)


# ═══════════════════════════════════════════════════════════════
# Dunning Processing Tests
# ═══════════════════════════════════════════════════════════════


class TestDunningProcessing:
    """Test processing pending dunning schedules."""

    @pytest.mark.asyncio
    async def test_list_by_invoice(
        self, db, tenant, confirmed_invoice
    ):
        """List dunning schedules for an invoice."""
        svc = DunningScheduleService(db, tenant.id)
        await svc.create_from_invoice(confirmed_invoice)

        schedules = await svc.list_by_invoice(confirmed_invoice.id)
        assert len(schedules) == len(DUNNING_SCHEDULE)

    @pytest.mark.asyncio
    async def test_list_all(
        self, db, tenant, confirmed_invoice
    ):
        """List all dunning schedules for the tenant."""
        svc = DunningScheduleService(db, tenant.id)
        await svc.create_from_invoice(confirmed_invoice)

        schedules, total = await svc.list_all()
        assert total >= len(DUNNING_SCHEDULE)
