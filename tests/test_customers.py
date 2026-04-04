"""
Customer service unit tests.

Coverage:
- List / get by ID (happy paths)
- Invite happy path
- Invite → 409 for pending invite
- Invite → 409 for already registered customer
- Tenant isolation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TenantStatus, UserRole
from app.core.security import generate_invite_token, hash_token
from app.exceptions.base import ConflictException, NotFoundException
from app.models.invite_token import InviteToken
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.company import CustomerInviteSchema
from app.services.company.customer import CustomerService


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def tenant_a(db: AsyncSession):
    t = Tenant(
        id=uuid.uuid4(),
        name="CustTenantA",
        slug=f"cust-a-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def tenant_b(db: AsyncSession):
    t = Tenant(
        id=uuid.uuid4(),
        name="CustTenantB",
        slug=f"cust-b-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def customers_a(db: AsyncSession, tenant_a: Tenant):
    customers = []
    for i in range(3):
        u = User(
            id=uuid.uuid4(),
            email=f"cust-a-{i}-{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hashed",
            role=UserRole.PORTAL_USER,
            tenant_id=tenant_a.id,
            name=f"Customer A-{i}",
        )
        db.add(u)
        customers.append(u)
    await db.flush()
    return customers


@pytest_asyncio.fixture
async def customer_b(db: AsyncSession, tenant_b: Tenant):
    u = User(
        id=uuid.uuid4(),
        email=f"cust-b-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed",
        role=UserRole.PORTAL_USER,
        tenant_id=tenant_b.id,
        name="Customer B",
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
def svc_a(db: AsyncSession, tenant_a: Tenant) -> CustomerService:
    return CustomerService(db, tenant_a.id)


@pytest_asyncio.fixture
def svc_b(db: AsyncSession, tenant_b: Tenant) -> CustomerService:
    return CustomerService(db, tenant_b.id)


# ═══════════════════════════════════════════════════════════════
# CRUD Happy Paths
# ═══════════════════════════════════════════════════════════════


class TestCustomerList:
    @pytest.mark.asyncio
    async def test_list_returns_portal_users(
        self, svc_a: CustomerService, customers_a,
    ):
        result = await svc_a.list_all()
        assert len(result) >= 3
        for u in result:
            assert u.role == UserRole.PORTAL_USER

    @pytest.mark.asyncio
    async def test_get_by_id(
        self, svc_a: CustomerService, customers_a,
    ):
        target = customers_a[0]
        customer = await svc_a.get_by_id(target.id)
        assert customer.id == target.id
        assert customer.name == target.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_raises_404(
        self, svc_a: CustomerService, customers_a,
    ):
        with pytest.raises(NotFoundException):
            await svc_a.get_by_id(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_count(
        self, svc_a: CustomerService, customers_a,
    ):
        count = await svc_a.count()
        assert count >= 3


# ═══════════════════════════════════════════════════════════════
# Invite
# ═══════════════════════════════════════════════════════════════


class TestCustomerInvite:
    @pytest.mark.asyncio
    async def test_invite_success(self, svc_a: CustomerService):
        email = f"newinvite-{uuid.uuid4().hex[:8]}@example.com"
        result = await svc_a.invite(CustomerInviteSchema(email=email))

        assert "invite_token" in result
        assert "invite_url" in result
        assert email not in result["invite_token"]  # token is random

    @pytest.mark.asyncio
    async def test_invite_pending_raises_409(
        self, db: AsyncSession, svc_a: CustomerService, tenant_a: Tenant,
    ):
        email = f"pending-{uuid.uuid4().hex[:8]}@example.com"

        # Create a pending invite manually
        raw = generate_invite_token()
        invite = InviteToken(
            tenant_id=tenant_a.id,
            email=email,
            role=UserRole.PORTAL_USER,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
        )
        db.add(invite)
        await db.flush()

        with pytest.raises(ConflictException, match="pending"):
            await svc_a.invite(CustomerInviteSchema(email=email))

    @pytest.mark.asyncio
    async def test_invite_already_registered_raises_409(
        self, svc_a: CustomerService, customers_a,
    ):
        existing_email = customers_a[0].email
        with pytest.raises(ConflictException, match="already has an account"):
            await svc_a.invite(
                CustomerInviteSchema(email=existing_email)
            )


# ═══════════════════════════════════════════════════════════════
# Tenant Isolation
# ═══════════════════════════════════════════════════════════════


class TestCustomerTenantIsolation:
    @pytest.mark.asyncio
    async def test_tenant_a_cannot_see_tenant_b_customers(
        self, svc_a: CustomerService, customers_a, customer_b,
    ):
        items = await svc_a.list_all()
        ids = {c.id for c in items}
        assert customer_b.id not in ids

    @pytest.mark.asyncio
    async def test_tenant_a_cannot_get_tenant_b_customer(
        self, svc_a: CustomerService, customer_b,
    ):
        with pytest.raises(NotFoundException):
            await svc_a.get_by_id(customer_b.id)
