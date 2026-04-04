"""
Product service unit tests.

Coverage:
- CRUD happy paths
- Unique name validation
- Soft-delete guard (active subscription lines)
- Variant CRUD
- Tenant isolation (company A ≠ company B)
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
from app.exceptions.base import ConflictException, NotFoundException, ValidationException
from app.models.plan import Plan
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.subscription import Subscription
from app.models.subscription_line import SubscriptionLine
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.company import ProductCreate, ProductUpdate, VariantCreate
from app.services.company.product import ProductService


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def tenant_a(db: AsyncSession):
    t = Tenant(
        id=uuid.uuid4(),
        name="Company A",
        slug=f"company-a-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def tenant_b(db: AsyncSession):
    t = Tenant(
        id=uuid.uuid4(),
        name="Company B",
        slug=f"company-b-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
def svc_a(db: AsyncSession, tenant_a: Tenant) -> ProductService:
    return ProductService(db, tenant_a.id)


@pytest_asyncio.fixture
def svc_b(db: AsyncSession, tenant_b: Tenant) -> ProductService:
    return ProductService(db, tenant_b.id)


# ═══════════════════════════════════════════════════════════════
# CRUD Happy Paths
# ═══════════════════════════════════════════════════════════════


class TestProductCRUD:
    @pytest.mark.asyncio
    async def test_create_product(self, svc_a: ProductService):
        dto = ProductCreate(
            name="Widget",
            type="physical",
            sales_price=Decimal("49.99"),
            cost_price=Decimal("20.00"),
        )
        product = await svc_a.create(dto)

        assert product.name == "Widget"
        assert product.type == "physical"
        assert product.sales_price == Decimal("49.99")
        assert product.cost_price == Decimal("20.00")
        assert product.id is not None

    @pytest.mark.asyncio
    async def test_list_products(self, svc_a: ProductService):
        for i in range(3):
            await svc_a.create(
                ProductCreate(
                    name=f"Product-{i}",
                    type="digital",
                    sales_price=Decimal("10.00"),
                    cost_price=Decimal("5.00"),
                )
            )
        items = await svc_a.list_all()
        assert len(items) >= 3

    @pytest.mark.asyncio
    async def test_get_by_id(self, svc_a: ProductService):
        product = await svc_a.create(
            ProductCreate(
                name="Findable",
                type="service",
                sales_price=Decimal("100.00"),
                cost_price=Decimal("0.00"),
            )
        )
        fetched = await svc_a.get_by_id(product.id)
        assert fetched.id == product.id
        assert fetched.name == "Findable"

    @pytest.mark.asyncio
    async def test_update_product(self, svc_a: ProductService):
        product = await svc_a.create(
            ProductCreate(
                name="OldName",
                type="physical",
                sales_price=Decimal("30.00"),
                cost_price=Decimal("10.00"),
            )
        )
        updated = await svc_a.update(
            product.id,
            ProductUpdate(name="NewName", sales_price=Decimal("35.00")),
        )
        assert updated.name == "NewName"
        assert updated.sales_price == Decimal("35.00")

    @pytest.mark.asyncio
    async def test_soft_delete(self, svc_a: ProductService):
        product = await svc_a.create(
            ProductCreate(
                name="Deletable",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        await svc_a.delete(product.id)
        with pytest.raises(NotFoundException):
            await svc_a.get_by_id(product.id)


# ═══════════════════════════════════════════════════════════════
# Validation
# ═══════════════════════════════════════════════════════════════


class TestProductValidation:
    @pytest.mark.asyncio
    async def test_duplicate_name_rejected(self, svc_a: ProductService):
        await svc_a.create(
            ProductCreate(
                name="Unique",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        with pytest.raises(ValidationException):
            await svc_a.create(
                ProductCreate(
                    name="Unique",
                    type="digital",
                    sales_price=Decimal("20.00"),
                    cost_price=Decimal("10.00"),
                )
            )

    @pytest.mark.asyncio
    async def test_duplicate_name_on_update_rejected(
        self, svc_a: ProductService,
    ):
        p1 = await svc_a.create(
            ProductCreate(
                name="First",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        p2 = await svc_a.create(
            ProductCreate(
                name="Second",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        with pytest.raises(ValidationException):
            await svc_a.update(p2.id, ProductUpdate(name="First"))

    @pytest.mark.asyncio
    async def test_same_name_allowed_across_tenants(
        self, svc_a: ProductService, svc_b: ProductService,
    ):
        await svc_a.create(
            ProductCreate(
                name="SharedName",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        # Same name in different tenant should work
        product_b = await svc_b.create(
            ProductCreate(
                name="SharedName",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        assert product_b.name == "SharedName"


# ═══════════════════════════════════════════════════════════════
# Soft-Delete Guard
# ═══════════════════════════════════════════════════════════════


class TestProductSoftDeleteGuard:
    @pytest.mark.asyncio
    async def test_cannot_delete_product_in_active_subscription(
        self, db: AsyncSession, svc_a: ProductService, tenant_a: Tenant,
    ):
        # Create product
        product = await svc_a.create(
            ProductCreate(
                name="InUse",
                type="physical",
                sales_price=Decimal("50.00"),
                cost_price=Decimal("20.00"),
            )
        )

        # Create a customer user
        customer = User(
            id=uuid.uuid4(),
            email=f"cust-{uuid.uuid4().hex[:8]}@test.test",
            password_hash="hashed",
            role="portal_user",
            tenant_id=tenant_a.id,
            name="Test Customer",
        )
        db.add(customer)
        await db.flush()

        # Create a plan
        plan = Plan(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            name="Test Plan",
            price=Decimal("29.99"),
            billing_period=BillingPeriod.MONTHLY,
            start_date=date(2026, 1, 1),
            features_json={},
            flags_json={},
        )
        db.add(plan)
        await db.flush()

        # Create active subscription
        sub = Subscription(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            number="SUB-001",
            customer_id=customer.id,
            plan_id=plan.id,
            start_date=date(2026, 1, 1),
            expiry_date=date(2027, 1, 1),
            status=SubscriptionStatus.ACTIVE,
        )
        db.add(sub)
        await db.flush()

        # Create subscription line using the product
        line = SubscriptionLine(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            subscription_id=sub.id,
            product_id=product.id,
            qty=1,
            unit_price=Decimal("50.00"),
        )
        db.add(line)
        await db.flush()

        # Should raise ConflictException
        with pytest.raises(ConflictException, match="active subscriptions"):
            await svc_a.delete(product.id)


# ═══════════════════════════════════════════════════════════════
# Variants
# ═══════════════════════════════════════════════════════════════


class TestProductVariants:
    @pytest.mark.asyncio
    async def test_create_and_list_variants(self, svc_a: ProductService):
        product = await svc_a.create(
            ProductCreate(
                name="VariantParent",
                type="physical",
                sales_price=Decimal("100.00"),
                cost_price=Decimal("50.00"),
            )
        )
        v1 = await svc_a.create_variant(
            product.id,
            VariantCreate(attribute="Color", value="Red", extra_price=Decimal("5.00")),
        )
        v2 = await svc_a.create_variant(
            product.id,
            VariantCreate(attribute="Size", value="Large"),
        )

        variants = await svc_a.list_variants(product.id)
        assert len(variants) >= 2

    @pytest.mark.asyncio
    async def test_delete_variant(self, svc_a: ProductService):
        product = await svc_a.create(
            ProductCreate(
                name="DVParent",
                type="physical",
                sales_price=Decimal("80.00"),
                cost_price=Decimal("40.00"),
            )
        )
        variant = await svc_a.create_variant(
            product.id,
            VariantCreate(attribute="Material", value="Leather"),
        )
        await svc_a.delete_variant(product.id, variant.id)

        # Variant should no longer appear
        variants = await svc_a.list_variants(product.id)
        ids = [v.id for v in variants]
        assert variant.id not in ids

    @pytest.mark.asyncio
    async def test_variant_wrong_product_raises_404(
        self, svc_a: ProductService,
    ):
        p1 = await svc_a.create(
            ProductCreate(
                name="P1",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        p2 = await svc_a.create(
            ProductCreate(
                name="P2",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        variant = await svc_a.create_variant(
            p1.id,
            VariantCreate(attribute="X", value="Y"),
        )
        with pytest.raises(NotFoundException):
            await svc_a.delete_variant(p2.id, variant.id)


# ═══════════════════════════════════════════════════════════════
# Tenant Isolation
# ═══════════════════════════════════════════════════════════════


class TestProductTenantIsolation:
    @pytest.mark.asyncio
    async def test_company_a_cannot_see_company_b_products(
        self, svc_a: ProductService, svc_b: ProductService,
    ):
        await svc_a.create(
            ProductCreate(
                name="A-Only",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        product_b = await svc_b.create(
            ProductCreate(
                name="B-Only",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )

        # Company A should not see Company B's product
        items_a = await svc_a.list_all()
        ids_a = {p.id for p in items_a}
        assert product_b.id not in ids_a

    @pytest.mark.asyncio
    async def test_company_a_cannot_get_company_b_product(
        self, svc_a: ProductService, svc_b: ProductService,
    ):
        product_b = await svc_b.create(
            ProductCreate(
                name="B-Secret",
                type="physical",
                sales_price=Decimal("10.00"),
                cost_price=Decimal("5.00"),
            )
        )
        with pytest.raises(NotFoundException):
            await svc_a.get_by_id(product_b.id)
