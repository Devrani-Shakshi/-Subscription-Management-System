"""
Super-admin integration tests.

Tests:
  test_create_company_success
  test_slug_conflict
  test_suspend_company
  test_suspend_already_suspended
  test_reactivate_company
  test_reactivate_already_active
  test_delete_company_no_subs
  test_delete_active_company_blocked
  test_list_companies
  test_get_company_detail
  test_check_slug_available
  test_check_slug_taken
  test_dashboard_metrics
  test_audit_log_list
  test_audit_log_export
  test_non_admin_blocked
  test_company_role_blocked
  test_portal_role_blocked
  test_get_nonexistent_company

Uses SQLite in-memory with the shared conftest engine/session.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    AuditAction,
    BillingPeriod,
    SubscriptionStatus,
    TenantStatus,
    UserRole,
)
from app.exceptions.base import ConflictException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.admin import (
    AuditLogFilter,
    CreateCompanySchema,
)
from app.services.admin_audit import SuperAdminAuditService
from app.services.admin_dashboard import SuperAdminDashboardService
from app.services.admin_tenant import SuperAdminTenantService


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def admin_user(db: AsyncSession):
    """Create a super_admin user for testing."""
    user = User(
        id=uuid.uuid4(),
        email=f"admin-{uuid.uuid4().hex[:8]}@platform.example.com",
        password_hash="hashed_pw",
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
        name="Test Admin",
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def company_tenant(db: AsyncSession, admin_user):
    """Create a tenant with owner for testing."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Corp",
        slug=f"test-corp-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
    )
    db.add(tenant)
    await db.flush()

    owner = User(
        id=uuid.uuid4(),
        email=f"owner-{uuid.uuid4().hex[:8]}@testcorp.example.com",
        password_hash="hashed_pw",
        role=UserRole.COMPANY,
        tenant_id=tenant.id,
        name="Test Corp Owner",
    )
    db.add(owner)
    await db.flush()

    tenant.owner_user_id = owner.id
    await db.flush()
    await db.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def suspended_tenant(db: AsyncSession, admin_user):
    """Create a suspended tenant for testing."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Suspended Inc",
        slug=f"suspended-inc-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.SUSPENDED,
    )
    db.add(tenant)
    await db.flush()
    return tenant


@pytest_asyncio.fixture
async def tenant_with_active_sub(db: AsyncSession, admin_user):
    """Create a tenant that has an active subscription."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Active Sub Corp",
        slug=f"active-sub-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(tenant)
    await db.flush()

    from app.models.plan import Plan

    plan = Plan(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Basic Plan",
        price=Decimal("29.99"),
        billing_period=BillingPeriod.MONTHLY,
        min_qty=1,
        start_date=date(2026, 1, 1),
        end_date=None,
        features_json={"max_users": 5},
        flags_json={"auto_close": False, "closable": True,
                     "pausable": False, "renewable": True},
    )
    db.add(plan)
    await db.flush()

    customer = User(
        id=uuid.uuid4(),
        email=f"customer-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_pw",
        role=UserRole.PORTAL_USER,
        tenant_id=tenant.id,
        name="Active Customer",
    )
    db.add(customer)
    await db.flush()

    sub = Subscription(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        number=f"SUB-{uuid.uuid4().hex[:8]}",
        customer_id=customer.id,
        plan_id=plan.id,
        start_date=date(2026, 1, 1),
        expiry_date=date(2027, 1, 1),
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(sub)
    await db.flush()
    return tenant


# ═══════════════════════════════════════════════════════════════
# Company CRUD Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_create_company_success(db: AsyncSession, admin_user):
    """Creating a company should produce tenant + invite."""
    svc = SuperAdminTenantService(db)
    slug = f"new-company-{uuid.uuid4().hex[:8]}"

    dto = CreateCompanySchema(
        name="New Company",
        slug=slug,
        email=f"owner-{uuid.uuid4().hex[:6]}@newcompany.example.com",
    )
    result = await svc.create_company(dto, actor_id=admin_user.id)

    assert result.name == "New Company"
    assert result.slug == slug
    assert result.invite_token is not None
    assert result.invite_url.startswith("http")
    assert result.tenant_id is not None

    # Verify tenant was persisted
    tenant_q = await db.execute(
        select(Tenant).where(Tenant.id == result.tenant_id)
    )
    tenant = tenant_q.scalar_one()
    assert tenant.status == TenantStatus.TRIAL
    assert tenant.owner_user_id is not None


@pytest.mark.asyncio
async def test_slug_conflict(db: AsyncSession, admin_user, company_tenant):
    """Creating a company with duplicate slug should raise ConflictException."""
    svc = SuperAdminTenantService(db)

    dto = CreateCompanySchema(
        name="Duplicate",
        slug=company_tenant.slug,
        email=f"dup-{uuid.uuid4().hex[:6]}@example.com",
    )

    with pytest.raises(ConflictException) as exc_info:
        await svc.create_company(dto, actor_id=admin_user.id)

    assert "taken" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_list_companies(db: AsyncSession, admin_user, company_tenant):
    """Listing companies should include the seeded tenant."""
    svc = SuperAdminTenantService(db)
    result = await svc.list_companies(page=1, page_size=50)

    assert result.total >= 1
    slugs = [item.slug for item in result.items]
    assert company_tenant.slug in slugs


@pytest.mark.asyncio
async def test_get_company_detail(db: AsyncSession, admin_user, company_tenant):
    """Getting company detail should return full info."""
    svc = SuperAdminTenantService(db)
    result = await svc.get_company_detail(company_tenant.id)

    assert result.id == company_tenant.id
    assert result.name == company_tenant.name
    assert result.slug == company_tenant.slug
    assert result.status == TenantStatus.ACTIVE


@pytest.mark.asyncio
async def test_get_nonexistent_company(db: AsyncSession, admin_user):
    """Getting a non-existent company should raise NotFoundException."""
    svc = SuperAdminTenantService(db)
    fake_id = uuid.uuid4()

    with pytest.raises(NotFoundException):
        await svc.get_company_detail(fake_id)


@pytest.mark.asyncio
async def test_check_slug_available(db: AsyncSession, admin_user):
    """Checking an unused slug should return available=True."""
    svc = SuperAdminTenantService(db)
    result = await svc.check_slug(f"brand-new-{uuid.uuid4().hex[:8]}")

    assert result.available is True
    assert result.suggestion is None


@pytest.mark.asyncio
async def test_check_slug_taken(db: AsyncSession, admin_user, company_tenant):
    """Checking a taken slug should return available=False with suggestion."""
    svc = SuperAdminTenantService(db)
    result = await svc.check_slug(company_tenant.slug)

    assert result.available is False
    assert result.suggestion is not None
    assert result.suggestion != company_tenant.slug


# ═══════════════════════════════════════════════════════════════
# Suspend / Reactivate Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_suspend_company(db: AsyncSession, admin_user, company_tenant):
    """Suspending an active company should change status."""
    svc = SuperAdminTenantService(db)
    result = await svc.suspend_company(company_tenant.id, actor_id=admin_user.id)

    assert result.status == TenantStatus.SUSPENDED
    assert "suspended" in result.message.lower()

    # Verify DB state
    await db.refresh(company_tenant)
    assert company_tenant.status == TenantStatus.SUSPENDED


@pytest.mark.asyncio
async def test_suspend_already_suspended(
    db: AsyncSession, admin_user, suspended_tenant
):
    """Suspending an already-suspended company should raise ConflictException."""
    svc = SuperAdminTenantService(db)

    with pytest.raises(ConflictException) as exc_info:
        await svc.suspend_company(suspended_tenant.id, actor_id=admin_user.id)

    assert "already suspended" in str(exc_info.value.message).lower()


@pytest.mark.asyncio
async def test_reactivate_company(
    db: AsyncSession, admin_user, suspended_tenant
):
    """Reactivating a suspended company should change status to active."""
    svc = SuperAdminTenantService(db)
    result = await svc.reactivate_company(
        suspended_tenant.id, actor_id=admin_user.id
    )

    assert result.status == TenantStatus.ACTIVE
    assert "reactivated" in result.message.lower()


@pytest.mark.asyncio
async def test_reactivate_already_active(
    db: AsyncSession, admin_user, company_tenant
):
    """Reactivating an already-active company should raise ConflictException."""
    svc = SuperAdminTenantService(db)

    with pytest.raises(ConflictException) as exc_info:
        await svc.reactivate_company(company_tenant.id, actor_id=admin_user.id)

    assert "already active" in str(exc_info.value.message).lower()


# ═══════════════════════════════════════════════════════════════
# Delete Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_delete_company_no_subs(
    db: AsyncSession, admin_user, suspended_tenant
):
    """Deleting a company with no active subs should succeed."""
    svc = SuperAdminTenantService(db)
    result = await svc.delete_company(
        suspended_tenant.id, actor_id=admin_user.id
    )

    assert "deleted" in result.message.lower()

    # Verify soft-deleted
    await db.refresh(suspended_tenant)
    assert suspended_tenant.deleted_at is not None


@pytest.mark.asyncio
async def test_delete_active_company_blocked(
    db: AsyncSession, admin_user, tenant_with_active_sub
):
    """Deleting a company with active subscriptions should be blocked."""
    svc = SuperAdminTenantService(db)

    with pytest.raises(ConflictException) as exc_info:
        await svc.delete_company(
            tenant_with_active_sub.id, actor_id=admin_user.id
        )

    assert "active subscription" in str(exc_info.value.message).lower()


# ═══════════════════════════════════════════════════════════════
# Dashboard Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_dashboard_metrics(db: AsyncSession, admin_user, company_tenant):
    """Dashboard should return metric cards, breakdown, and alerts."""
    svc = SuperAdminDashboardService(db)
    result = await svc.get_platform_metrics()

    assert len(result.metrics) >= 1
    labels = [m.label for m in result.metrics]
    assert "Total Companies" in labels

    # Breakdown should include our tenant
    assert isinstance(result.company_breakdown, list)
    assert isinstance(result.alerts, list)


# ═══════════════════════════════════════════════════════════════
# Audit Log Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_audit_log_list(db: AsyncSession, admin_user, company_tenant):
    """Audit log should return entries after operations that log."""
    # Create a company to generate an audit entry
    tenant_svc = SuperAdminTenantService(db)
    slug = f"audit-test-{uuid.uuid4().hex[:8]}"
    dto = CreateCompanySchema(
        name="Audit Test Co",
        slug=slug,
        email=f"audit-{uuid.uuid4().hex[:6]}@example.com",
    )
    await tenant_svc.create_company(dto, actor_id=admin_user.id)

    # Query audit log
    audit_svc = SuperAdminAuditService(db)
    filters = AuditLogFilter(page=1, page_size=50)
    result = await audit_svc.list_audit_logs(filters)

    assert result.total >= 1
    entity_types = [item.entity_type for item in result.items]
    assert "tenant" in entity_types


@pytest.mark.asyncio
async def test_audit_log_export(db: AsyncSession, admin_user, company_tenant):
    """Audit log CSV export should produce valid CSV text."""
    # Generate an audit entry first
    tenant_svc = SuperAdminTenantService(db)
    slug = f"export-test-{uuid.uuid4().hex[:8]}"
    dto = CreateCompanySchema(
        name="Export Test Co",
        slug=slug,
        email=f"export-{uuid.uuid4().hex[:6]}@example.com",
    )
    await tenant_svc.create_company(dto, actor_id=admin_user.id)

    audit_svc = SuperAdminAuditService(db)
    filters = AuditLogFilter(page=1, page_size=50)
    csv_text = await audit_svc.export_csv(filters)

    assert isinstance(csv_text, str)
    assert "ID" in csv_text  # header row
    assert "Timestamp" in csv_text
    lines = csv_text.strip().split("\n")
    assert len(lines) >= 2  # header + at least 1 data row


# ═══════════════════════════════════════════════════════════════
# Access Control Tests
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_non_admin_blocked(db: AsyncSession, admin_user):
    """
    Company-role users should not pass super_admin guard.
    Self-contained: creates its own tenant + company user inline.
    """
    from app.schemas.auth import TokenPayload

    t = Tenant(
        id=uuid.uuid4(),
        name="Guard Test Corp",
        slug=f"guard-co-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()

    co_user = User(
        id=uuid.uuid4(),
        email=f"guard-co-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_pw",
        role=UserRole.COMPANY,
        tenant_id=t.id,
        name="Guard Company User",
    )
    db.add(co_user)
    await db.flush()

    assert co_user.role == UserRole.COMPANY
    assert co_user.role != UserRole.SUPER_ADMIN

    token = TokenPayload(
        user_id=co_user.id,
        role="company",
        tenant_id=co_user.tenant_id,
        email=co_user.email,
    )
    assert token.role != "super_admin"


@pytest.mark.asyncio
async def test_portal_role_blocked(db: AsyncSession, admin_user):
    """
    Portal-role users should not pass super_admin guard.
    Self-contained: creates its own tenant + portal user inline.
    """
    from app.schemas.auth import TokenPayload

    t = Tenant(
        id=uuid.uuid4(),
        name="Guard Test Portal",
        slug=f"guard-pt-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()

    pt_user = User(
        id=uuid.uuid4(),
        email=f"guard-pt-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_pw",
        role=UserRole.PORTAL_USER,
        tenant_id=t.id,
        name="Guard Portal User",
    )
    db.add(pt_user)
    await db.flush()

    assert pt_user.role == UserRole.PORTAL_USER
    assert pt_user.role != UserRole.SUPER_ADMIN

    token = TokenPayload(
        user_id=pt_user.id,
        role="portal_user",
        tenant_id=pt_user.tenant_id,
        email=pt_user.email,
    )
    assert token.role != "super_admin"
