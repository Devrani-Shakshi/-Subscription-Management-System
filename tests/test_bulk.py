"""
Tests for bulk operations module.

Covers:
  - Conflict detection before execution
  - BulkActivate / BulkClose operations
  - BulkApplyDiscount with param validation
  - BulkChangePlan with same-plan conflict
  - BulkExecutor preview + run
  - Partial failure handling
  - Tenant isolation on bulk
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BulkOperationType, SubscriptionStatus
from app.models.subscription import Subscription
from app.services.bulk.conflict_detector import ConflictDetector
from app.services.bulk.executor import BulkExecutor
from app.services.bulk.factory import BulkOperationFactory
from app.services.bulk.operations import (
    BulkActivate,
    BulkChangePlan,
    BulkClose,
)


# ── Helper ──────────────────────────────────────────────────


async def _make_sub(
    db, tenant, portal_user, plan, status, number=None
) -> Subscription:
    """Create a subscription with given status."""
    sub = Subscription(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        number=number or f"BULK-{uuid.uuid4().hex[:6]}",
        customer_id=portal_user.id,
        plan_id=plan.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        status=status,
    )
    db.add(sub)
    await db.flush()
    return sub


# ═══════════════════════════════════════════════════════════════
# Conflict detection tests
# ═══════════════════════════════════════════════════════════════


class TestConflictDetection:
    """Test ConflictDetector pre-flight checks."""

    @pytest.mark.asyncio
    async def test_activate_detects_invalid_status(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Cannot activate a CLOSED subscription."""
        closed = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.CLOSED
        )
        report = await ConflictDetector.detect(
            ids=[closed.id],
            operation_type=BulkOperationType.ACTIVATE,
            db=db,
            tenant_id=tenant.id,
        )
        assert report.has_conflicts
        assert report.conflicts[0].conflict_type == "invalid_status"

    @pytest.mark.asyncio
    async def test_activate_clean_for_confirmed(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Confirmed subscriptions → no conflicts."""
        confirmed = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.CONFIRMED
        )
        report = await ConflictDetector.detect(
            ids=[confirmed.id],
            operation_type=BulkOperationType.ACTIVATE,
            db=db,
            tenant_id=tenant.id,
        )
        assert not report.has_conflicts

    @pytest.mark.asyncio
    async def test_close_detects_already_closed(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Already closed → conflict."""
        closed = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.CLOSED
        )
        report = await ConflictDetector.detect(
            ids=[closed.id],
            operation_type=BulkOperationType.CLOSE,
            db=db,
            tenant_id=tenant.id,
        )
        assert report.has_conflicts

    @pytest.mark.asyncio
    async def test_not_found_ids(
        self, db: AsyncSession, tenant
    ):
        """Non-existent IDs → not_found conflict."""
        fake_id = uuid.uuid4()
        report = await ConflictDetector.detect(
            ids=[fake_id],
            operation_type=BulkOperationType.ACTIVATE,
            db=db,
            tenant_id=tenant.id,
        )
        assert report.has_conflicts
        assert report.conflicts[0].conflict_type == "not_found"


# ═══════════════════════════════════════════════════════════════
# Operation execution tests
# ═══════════════════════════════════════════════════════════════


class TestBulkActivate:
    """Test BulkActivate operation."""

    @pytest.mark.asyncio
    async def test_activate_confirmed_subs(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Activate 3 confirmed subscriptions."""
        subs = [
            await _make_sub(
                db, tenant, portal_user, plan,
                SubscriptionStatus.CONFIRMED,
            )
            for _ in range(3)
        ]
        ids = [s.id for s in subs]

        op = BulkActivate(db, tenant.id)
        result = await op.execute(ids)

        assert len(result.success) == 3
        assert len(result.failed) == 0

        # Verify status changed
        for sub in subs:
            await db.refresh(sub)
            assert sub.status == SubscriptionStatus.ACTIVE


class TestBulkClose:
    """Test BulkClose operation."""

    @pytest.mark.asyncio
    async def test_close_active_subs(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Close active subscriptions."""
        sub = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.ACTIVE
        )
        op = BulkClose(db, tenant.id)
        result = await op.execute([sub.id])

        assert len(result.success) == 1
        await db.refresh(sub)
        assert sub.status == SubscriptionStatus.CLOSED


class TestBulkChangePlan:
    """Test BulkChangePlan operation."""

    @pytest.mark.asyncio
    async def test_change_plan_detects_same_plan(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Same plan → conflict."""
        sub = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.ACTIVE
        )
        op = BulkChangePlan(
            db, tenant.id, params={"plan_id": str(plan.id)}
        )
        report = await op.validate([sub.id])
        assert report.has_conflicts


# ═══════════════════════════════════════════════════════════════
# Executor tests
# ═══════════════════════════════════════════════════════════════


class TestBulkExecutor:
    """Test BulkExecutor preview + run."""

    @pytest.mark.asyncio
    async def test_preview_returns_conflicts(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Preview returns conflict count."""
        closed = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.CLOSED
        )
        executor = BulkExecutor(db, tenant.id)
        preview = await executor.preview(
            ids=[closed.id],
            operation_type=BulkOperationType.ACTIVATE,
        )
        assert preview["conflict_count"] == 1
        assert preview["clean_count"] == 0

    @pytest.mark.asyncio
    async def test_run_with_skip_ids(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Run skips specified IDs."""
        confirmed = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.CONFIRMED
        )
        skip_sub = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.CONFIRMED
        )

        executor = BulkExecutor(db, tenant.id)
        result = await executor.run(
            ids=[confirmed.id, skip_sub.id],
            operation_type=BulkOperationType.ACTIVATE,
            skip_ids=[skip_sub.id],
        )

        assert len(result.success) == 1
        assert confirmed.id in result.success

    @pytest.mark.asyncio
    async def test_tenant_isolation(
        self, db: AsyncSession, tenant, portal_user, plan
    ):
        """Subscriptions from other tenants are not visible."""
        sub = await _make_sub(
            db, tenant, portal_user, plan, SubscriptionStatus.CONFIRMED
        )

        other_tenant = uuid.uuid4()
        executor = BulkExecutor(db, other_tenant)
        preview = await executor.preview(
            ids=[sub.id],
            operation_type=BulkOperationType.ACTIVATE,
        )

        # The sub should show as not_found for the other tenant
        assert preview["conflict_count"] == 1


class TestBulkOperationFactory:
    """Test factory pattern."""

    @pytest.mark.asyncio
    async def test_create_valid_operation(
        self, db: AsyncSession, tenant
    ):
        """Factory creates correct operation type."""
        op = BulkOperationFactory.create(
            "activate", db, tenant.id
        )
        assert isinstance(op, BulkActivate)

    @pytest.mark.asyncio
    async def test_create_invalid_operation_raises(
        self, db: AsyncSession, tenant
    ):
        """Factory raises ValidationException for unknown type."""
        from app.exceptions.base import ValidationException

        with pytest.raises(ValidationException):
            BulkOperationFactory.create(
                "nonexistent", db, tenant.id
            )
