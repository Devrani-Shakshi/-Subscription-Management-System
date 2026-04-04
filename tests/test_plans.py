"""
Plan service unit tests.

Coverage:
- CRUD happy paths
- Preview endpoint
- Soft-delete guard (active subscriptions)
- Tenant isolation
- Validation (end_date > start_date enforced at schema level)
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BillingPeriod,
    SubscriptionStatus,
    TenantStatus,
)
from app.exceptions.base import ConflictException, NotFoundException
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.company import PlanCreate, PlanUpdate
from app.services.company.plan import PlanService


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def tenant_a(db: AsyncSession):
    t = Tenant(
        id=uuid.uuid4(),
        name="PlanTenantA",
        slug=f"plan-a-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def tenant_b(db: AsyncSession):
    t = Tenant(
        id=uuid.uuid4(),
        name="PlanTenantB",
        slug=f"plan-b-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
def svc_a(db: AsyncSession, tenant_a: Tenant) -> PlanService:
    return PlanService(db, tenant_a.id)


@pytest_asyncio.fixture
def svc_b(db: AsyncSession, tenant_b: Tenant) -> PlanService:
    return PlanService(db, tenant_b.id)


def _plan_dto(**overrides) -> PlanCreate:
    defaults = dict(
        name="Standard",
        price=Decimal("29.99"),
        billing_period=BillingPeriod.MONTHLY,
        start_date=date(2026, 1, 1),
    )
    defaults.update(overrides)
    return PlanCreate(**defaults)


# ═══════════════════════════════════════════════════════════════
# CRUD Happy Paths
# ═══════════════════════════════════════════════════════════════


class TestPlanCRUD:
    @pytest.mark.asyncio
    async def test_create_plan(self, svc_a: PlanService):
        plan = await svc_a.create(_plan_dto())
        assert plan.name == "Standard"
        assert plan.price == Decimal("29.99")
        assert plan.billing_period == BillingPeriod.MONTHLY

    @pytest.mark.asyncio
    async def test_list_plans(self, svc_a: PlanService):
        for i in range(3):
            await svc_a.create(_plan_dto(name=f"Plan-{i}"))
        items = await svc_a.list_all()
        assert len(items) >= 3

    @pytest.mark.asyncio
    async def test_get_by_id(self, svc_a: PlanService):
        plan = await svc_a.create(_plan_dto(name="Findable"))
        fetched = await svc_a.get_by_id(plan.id)
        assert fetched.name == "Findable"

    @pytest.mark.asyncio
    async def test_update_plan(self, svc_a: PlanService):
        plan = await svc_a.create(_plan_dto(name="Old"))
        updated = await svc_a.update(
            plan.id,
            PlanUpdate(name="New", price=Decimal("49.99")),
        )
        assert updated.name == "New"
        assert updated.price == Decimal("49.99")

    @pytest.mark.asyncio
    async def test_soft_delete(self, svc_a: PlanService):
        plan = await svc_a.create(_plan_dto(name="Deletable"))
        await svc_a.delete(plan.id)
        with pytest.raises(NotFoundException):
            await svc_a.get_by_id(plan.id)


# ═══════════════════════════════════════════════════════════════
# Preview
# ═══════════════════════════════════════════════════════════════


class TestPlanPreview:
    @pytest.mark.asyncio
    async def test_preview_returns_card_data(self, svc_a: PlanService):
        plan = await svc_a.create(
            _plan_dto(
                name="Premium",
                features_json={"max_users": 50, "api_access": True},
                flags_json={"closable": True, "pausable": True, "renewable": True, "auto_close": False},
            )
        )
        preview = await svc_a.get_preview(plan.id)
        assert preview.name == "Premium"
        assert preview.features["max_users"] == 50
        assert preview.flags["pausable"] is True


# ═══════════════════════════════════════════════════════════════
# Soft-Delete Guard
# ═══════════════════════════════════════════════════════════════


class TestPlanSoftDeleteGuard:
    @pytest.mark.asyncio
    async def test_cannot_delete_plan_with_active_subs(
        self, db: AsyncSession, svc_a: PlanService, tenant_a: Tenant,
    ):
        plan = await svc_a.create(_plan_dto(name="ActivePlan"))

        customer = User(
            id=uuid.uuid4(),
            email=f"cust-plan-{uuid.uuid4().hex[:8]}@test.test",
            password_hash="hashed",
            role="portal_user",
            tenant_id=tenant_a.id,
            name="Customer",
        )
        db.add(customer)
        await db.flush()

        sub = Subscription(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            number="SUB-P001",
            customer_id=customer.id,
            plan_id=plan.id,
            start_date=date(2026, 1, 1),
            expiry_date=date(2027, 1, 1),
            status=SubscriptionStatus.ACTIVE,
        )
        db.add(sub)
        await db.flush()

        with pytest.raises(ConflictException, match="active subscriptions"):
            await svc_a.delete(plan.id)


# ═══════════════════════════════════════════════════════════════
# Validation (schema level)
# ═══════════════════════════════════════════════════════════════


class TestPlanValidation:
    def test_end_date_must_be_after_start(self):
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            PlanCreate(
                name="Invalid",
                price=Decimal("10.00"),
                billing_period=BillingPeriod.MONTHLY,
                start_date=date(2026, 6, 1),
                end_date=date(2026, 1, 1),  # before start
            )

    def test_price_must_be_positive(self):
        with pytest.raises(ValueError):
            PlanCreate(
                name="Free",
                price=Decimal("0.00"),  # gt=0 fails
                billing_period=BillingPeriod.MONTHLY,
                start_date=date(2026, 1, 1),
            )


# ═══════════════════════════════════════════════════════════════
# Tenant Isolation
# ═══════════════════════════════════════════════════════════════


class TestPlanTenantIsolation:
    @pytest.mark.asyncio
    async def test_tenant_a_cannot_see_tenant_b_plans(
        self, svc_a: PlanService, svc_b: PlanService,
    ):
        await svc_a.create(_plan_dto(name="A-Plan"))
        plan_b = await svc_b.create(_plan_dto(name="B-Plan"))

        items_a = await svc_a.list_all()
        ids_a = {p.id for p in items_a}
        assert plan_b.id not in ids_a

    @pytest.mark.asyncio
    async def test_tenant_a_cannot_get_tenant_b_plan(
        self, svc_a: PlanService, svc_b: PlanService,
    ):
        plan_b = await svc_b.create(_plan_dto(name="B-Secret"))
        with pytest.raises(NotFoundException):
            await svc_a.get_by_id(plan_b.id)
