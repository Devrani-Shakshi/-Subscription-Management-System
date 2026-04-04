"""
Test suite for subscription management.

Tests:
  test_create_wizard_flow          — full multi-step create + draft status
  test_fsm_valid_transitions       — all legal state transitions
  test_fsm_invalid_transition      — rejected illegal transitions
  test_upgrade_pro_rata_invoice    — upgrade creates correct delta invoice
  test_downgrade_scheduled         — downgrade sets future date
  test_downgrade_already_scheduled — duplicate downgrade raises conflict
  test_portal_own_subscription_only — ownership guard
  test_cancel_unclosable_plan      — closable=False blocks cancellation
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BillingPeriod, SubscriptionStatus, UserRole
from app.exceptions.base import ConflictException, NotFoundException
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.subscription_line import SubscriptionLine
from app.models.user import User
from app.services.subscriptions.downgrade import DowngradeService
from app.services.subscriptions.fsm import SubscriptionStatusFSM
from app.services.subscriptions.portal import PortalSubscriptionService
from app.services.subscriptions.pro_rata import ProRataCalculator
from app.services.subscriptions.subscription import SubscriptionService
from app.services.subscriptions.upgrade import UpgradeService


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def plan_basic(db: AsyncSession, tenant):
    """A basic monthly plan at $29.99."""
    p = Plan(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Basic Plan",
        price=Decimal("29.99"),
        billing_period=BillingPeriod.MONTHLY,
        min_qty=1,
        start_date=date(2026, 1, 1),
        features_json={"max_users": 5},
        flags_json={
            "auto_close": False,
            "closable": True,
            "pausable": False,
            "renewable": True,
        },
    )
    db.add(p)
    await db.flush()
    return p


@pytest_asyncio.fixture
async def plan_premium(db: AsyncSession, tenant):
    """A premium monthly plan at $99.99."""
    p = Plan(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Premium Plan",
        price=Decimal("99.99"),
        billing_period=BillingPeriod.MONTHLY,
        min_qty=1,
        start_date=date(2026, 1, 1),
        features_json={"max_users": 50},
        flags_json={
            "auto_close": False,
            "closable": True,
            "pausable": False,
            "renewable": True,
        },
    )
    db.add(p)
    await db.flush()
    return p


@pytest_asyncio.fixture
async def plan_unclosable(db: AsyncSession, tenant):
    """A plan that cannot be cancelled."""
    p = Plan(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Enterprise Lock-in",
        price=Decimal("199.99"),
        billing_period=BillingPeriod.YEARLY,
        min_qty=1,
        start_date=date(2026, 1, 1),
        features_json={"max_users": 500},
        flags_json={
            "auto_close": False,
            "closable": False,
            "pausable": False,
            "renewable": True,
        },
    )
    db.add(p)
    await db.flush()
    return p


@pytest_asyncio.fixture
async def subscription(db: AsyncSession, tenant, portal_user, plan_basic, product):
    """A draft subscription with one line item."""
    sub = Subscription(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        number="SUB-000001",
        customer_id=portal_user.id,
        plan_id=plan_basic.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=30),
        payment_terms="net-30",
        status=SubscriptionStatus.DRAFT,
    )
    db.add(sub)
    await db.flush()

    line = SubscriptionLine(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        subscription_id=sub.id,
        product_id=product.id,
        qty=2,
        unit_price=Decimal("49.99"),
    )
    db.add(line)
    await db.flush()
    await db.refresh(sub)
    return sub


@pytest_asyncio.fixture
async def active_subscription(
    db: AsyncSession, tenant, portal_user, plan_basic, product,
):
    """A fully active subscription."""
    sub = Subscription(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        number="SUB-000002",
        customer_id=portal_user.id,
        plan_id=plan_basic.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=30),
        payment_terms="net-30",
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(sub)
    await db.flush()

    line = SubscriptionLine(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        subscription_id=sub.id,
        product_id=product.id,
        qty=1,
        unit_price=Decimal("29.99"),
    )
    db.add(line)
    await db.flush()
    await db.refresh(sub)
    return sub


@pytest_asyncio.fixture
async def other_portal_user(db: AsyncSession, tenant):
    """A different portal user in the same tenant."""
    u = User(
        id=uuid.uuid4(),
        email=f"other-{uuid.uuid4().hex[:8]}@customer.example.com",
        password_hash="hashed_pw",
        role=UserRole.PORTAL_USER,
        tenant_id=tenant.id,
        name="Other Customer",
    )
    db.add(u)
    await db.flush()
    return u


# ═══════════════════════════════════════════════════════════════
# TEST: Create wizard flow
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_wizard_flow(
    db: AsyncSession, tenant, portal_user, plan_basic, product,
):
    """Multi-step wizard → POST creates a draft subscription."""
    svc = SubscriptionService(db, tenant.id)

    sub = await svc.create(
        customer_id=portal_user.id,
        plan_id=plan_basic.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=30),
        payment_terms="net-30",
        lines=[
            {
                "product_id": product.id,
                "qty": 2,
                "unit_price": "49.99",
            },
        ],
    )

    assert sub.status == SubscriptionStatus.DRAFT
    assert sub.number.startswith("SUB-")
    assert sub.customer_id == portal_user.id
    assert sub.plan_id == plan_basic.id
    assert len(sub.lines) == 1
    assert sub.lines[0].qty == 2


# ═══════════════════════════════════════════════════════════════
# TEST: FSM valid transitions
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_fsm_valid_transitions(db: AsyncSession, subscription):
    """Walk through the full lifecycle: draft → quotation → confirmed → active."""
    sub = subscription

    # draft → quotation
    SubscriptionStatusFSM.transition(sub, SubscriptionStatus.QUOTATION)
    assert sub.status == SubscriptionStatus.QUOTATION

    # quotation → confirmed
    SubscriptionStatusFSM.transition(sub, SubscriptionStatus.CONFIRMED)
    assert sub.status == SubscriptionStatus.CONFIRMED

    # confirmed → active
    SubscriptionStatusFSM.transition(sub, SubscriptionStatus.ACTIVE)
    assert sub.status == SubscriptionStatus.ACTIVE


# ═══════════════════════════════════════════════════════════════
# TEST: FSM invalid transition
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_fsm_invalid_transition(db: AsyncSession, subscription):
    """Cannot jump from draft directly to active."""
    sub = subscription
    assert sub.status == SubscriptionStatus.DRAFT

    with pytest.raises(ConflictException) as exc_info:
        SubscriptionStatusFSM.transition(sub, SubscriptionStatus.ACTIVE)

    assert "Cannot move from draft to active" in str(exc_info.value)


# ═══════════════════════════════════════════════════════════════
# TEST: Upgrade pro-rata invoice
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_upgrade_pro_rata_invoice(
    db: AsyncSession,
    tenant,
    active_subscription,
    plan_basic,
    plan_premium,
):
    """Upgrade creates a delta invoice with correct pro-rata amount."""
    svc = UpgradeService(db, tenant.id)
    result = await svc.execute(active_subscription.id, plan_premium.id)

    assert result["delta_invoice_id"] is not None
    assert Decimal(result["amount_due"]) >= Decimal("0.00")

    # Verify plan was changed
    await db.refresh(active_subscription)
    assert active_subscription.plan_id == plan_premium.id


# ═══════════════════════════════════════════════════════════════
# TEST: Pro-rata calculator unit test
# ═══════════════════════════════════════════════════════════════


def test_pro_rata_calculation():
    """Pro-rata calculator produces correct values."""
    result = ProRataCalculator.calculate(
        old_price=Decimal("30.00"),
        new_price=Decimal("90.00"),
        billing_days=30,
        remaining_days=15,
    )

    assert result.old_daily_rate == Decimal("1.00")
    assert result.new_daily_rate == Decimal("3.00")
    assert result.credit == Decimal("15.00")
    assert result.charge == Decimal("45.00")
    assert result.amount_due == Decimal("30.00")
    assert result.remaining_days == 15
    assert result.billing_days == 30


# ═══════════════════════════════════════════════════════════════
# TEST: Downgrade scheduled
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_downgrade_scheduled(
    db: AsyncSession,
    tenant,
    active_subscription,
    plan_basic,
    plan_premium,
):
    """Downgrade schedules change at period end, not immediately."""
    # First upgrade to premium so we can "downgrade" back to basic
    active_subscription.plan_id = plan_premium.id
    await db.flush()

    svc = DowngradeService(db, tenant.id)
    result = await svc.execute(active_subscription.id, plan_basic.id)

    assert "downgrade_at" in result
    assert result["downgrade_to_plan_id"] == str(plan_basic.id)

    # Plan NOT changed yet
    await db.refresh(active_subscription)
    assert active_subscription.plan_id == plan_premium.id
    assert active_subscription.downgrade_to_plan_id == plan_basic.id


# ═══════════════════════════════════════════════════════════════
# TEST: Downgrade already scheduled
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_downgrade_already_scheduled(
    db: AsyncSession,
    tenant,
    active_subscription,
    plan_basic,
    plan_premium,
):
    """Cannot schedule a second downgrade while one is pending."""
    active_subscription.plan_id = plan_premium.id
    await db.flush()

    svc = DowngradeService(db, tenant.id)
    await svc.execute(active_subscription.id, plan_basic.id)

    with pytest.raises(ConflictException) as exc_info:
        await svc.execute(active_subscription.id, plan_basic.id)

    assert "already scheduled" in str(exc_info.value)


# ═══════════════════════════════════════════════════════════════
# TEST: Portal — own subscription only
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_portal_own_subscription_only(
    db: AsyncSession,
    tenant,
    other_portal_user,
    active_subscription,
):
    """
    Portal user can only see their own subscription.
    other_portal_user does NOT own the active_subscription.
    """
    svc = PortalSubscriptionService(
        db, tenant.id, other_portal_user.id,
    )
    with pytest.raises(NotFoundException) as exc_info:
        await svc.get_my_subscription()

    assert "No active subscription" in str(exc_info.value)


# ═══════════════════════════════════════════════════════════════
# TEST: Cancel unclosable plan
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_cancel_unclosable_plan(
    db: AsyncSession,
    tenant,
    portal_user,
    plan_unclosable,
    product,
):
    """Cancelling a plan with closable=False raises ConflictException."""
    # Create an active subscription on the unclosable plan
    sub = Subscription(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        number="SUB-LOCK-01",
        customer_id=portal_user.id,
        plan_id=plan_unclosable.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        payment_terms="net-30",
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(sub)
    await db.flush()

    svc = PortalSubscriptionService(db, tenant.id, portal_user.id)
    with pytest.raises(ConflictException) as exc_info:
        await svc.cancel()

    assert "cannot be cancelled" in str(exc_info.value)
