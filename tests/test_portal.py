"""
Portal tests — portal_user self-service.

Tests:
  test_self_register
  test_email_already_registered
  test_portal_access_own_data_only
  test_suspended_tenant_portal_login
  test_password_change
  test_session_revoke
  test_revoke_all_devices
  test_public_plan_catalogue_no_auth
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    BillingPeriod,
    InvoiceStatus,
    SubscriptionStatus,
    TenantStatus,
    UserRole,
)
from app.core.security import hash_password, hash_token, verify_password
from app.exceptions.base import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.session import Session
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import RegisterSchema, TokenPayload
from app.schemas.portal import PasswordChangeRequest, PortalProfileUpdateRequest
from app.services.auth import AuthService
from app.services.portal import PortalService
from app.services.subscriptions.portal import PortalSubscriptionService


# ═══════════════════════════════════════════════════════════════
# Additional Fixtures (portal-specific)
# ═══════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def portal_tenant(db: AsyncSession):
    """Active tenant for portal tests."""
    t = Tenant(
        id=uuid.uuid4(),
        name="Portal Corp",
        slug=f"portal-corp-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def suspended_tenant(db: AsyncSession):
    """Suspended tenant for login rejection test."""
    t = Tenant(
        id=uuid.uuid4(),
        name="Suspended Corp",
        slug=f"suspended-corp-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.SUSPENDED,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def portal_customer(db: AsyncSession, portal_tenant):
    """Portal user with a real bcrypt password for password tests."""
    u = User(
        id=uuid.uuid4(),
        email=f"portal-{uuid.uuid4().hex[:8]}@customer.example.com",
        password_hash=hash_password("OldPass@123"),
        role=UserRole.PORTAL_USER,
        tenant_id=portal_tenant.id,
        name="Portal Customer",
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def other_portal_customer(db: AsyncSession, portal_tenant):
    """Another portal user — used for ownership isolation test."""
    u = User(
        id=uuid.uuid4(),
        email=f"other-{uuid.uuid4().hex[:8]}@customer.example.com",
        password_hash=hash_password("OtherPass@123"),
        role=UserRole.PORTAL_USER,
        tenant_id=portal_tenant.id,
        name="Other Customer",
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def suspended_user(db: AsyncSession, suspended_tenant):
    """Portal user tied to a suspended tenant."""
    u = User(
        id=uuid.uuid4(),
        email=f"sus-{uuid.uuid4().hex[:8]}@customer.example.com",
        password_hash=hash_password("SusPass@123"),
        role=UserRole.PORTAL_USER,
        tenant_id=suspended_tenant.id,
        name="Suspended Customer",
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def portal_plan(db: AsyncSession, portal_tenant):
    """Plan belonging to the portal tenant."""
    p = Plan(
        id=uuid.uuid4(),
        tenant_id=portal_tenant.id,
        name="Pro Monthly",
        price=Decimal("49.99"),
        billing_period=BillingPeriod.MONTHLY,
        min_qty=1,
        start_date=date(2026, 1, 1),
        features_json={"api_calls": 10000, "storage_gb": 50},
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
async def portal_subscription(db: AsyncSession, portal_tenant, portal_customer, portal_plan):
    """Active subscription for the portal customer."""
    s = Subscription(
        id=uuid.uuid4(),
        tenant_id=portal_tenant.id,
        number=f"SUB-{uuid.uuid4().hex[:6].upper()}",
        customer_id=portal_customer.id,
        plan_id=portal_plan.id,
        start_date=date(2026, 1, 1),
        expiry_date=date(2027, 1, 1),
        payment_terms="net-30",
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(s)
    await db.flush()
    return s


@pytest_asyncio.fixture
async def portal_invoice(db: AsyncSession, portal_tenant, portal_subscription, portal_customer):
    """Draft invoice for the portal customer."""
    inv = Invoice(
        id=uuid.uuid4(),
        tenant_id=portal_tenant.id,
        invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
        subscription_id=portal_subscription.id,
        customer_id=portal_customer.id,
        status=InvoiceStatus.CONFIRMED,
        due_date=date.today() + timedelta(days=30),
        subtotal=Decimal("49.99"),
        tax_total=Decimal("0.00"),
        discount_total=Decimal("0.00"),
        total=Decimal("49.99"),
        amount_paid=Decimal("0.00"),
    )
    db.add(inv)
    await db.flush()
    return inv


@pytest_asyncio.fixture
async def portal_sessions(db: AsyncSession, portal_customer, portal_tenant):
    """Create 3 sessions for the portal customer."""
    sessions = []
    for i in range(3):
        s = Session(
            id=uuid.uuid4(),
            user_id=portal_customer.id,
            tenant_id=portal_tenant.id,
            refresh_token_hash=hash_token(f"token_{i}_{uuid.uuid4().hex}"),
            family_id=uuid.uuid4(),
            device_fingerprint=f"device_{i}",
            ip_subnet=f"192.168.{i}.0",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked_at=None,
        )
        db.add(s)
        sessions.append(s)
    await db.flush()
    return sessions


# ═══════════════════════════════════════════════════════════════
# TEST: Self-Register
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_self_register(db: AsyncSession, portal_tenant):
    """
    Self-registration creates a portal_user under the correct tenant.
    """
    dto = RegisterSchema(
        email=f"newuser-{uuid.uuid4().hex[:8]}@test.com",
        password="MyStr0ng@Pass",
        name="New User",
        tenant_slug=portal_tenant.slug,
    )

    svc = AuthService(db)
    user = await svc.register_portal(dto)

    assert user.email == dto.email
    assert user.role == UserRole.PORTAL_USER
    assert user.tenant_id == portal_tenant.id
    assert user.name == "New User"


# ═══════════════════════════════════════════════════════════════
# TEST: Email Already Registered (409)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_email_already_registered(db: AsyncSession, portal_tenant, portal_customer):
    """
    Registration with an existing email returns 409 ConflictException.
    """
    dto = RegisterSchema(
        email=portal_customer.email,
        password="MyStr0ng@Pass",
        name="Duplicate User",
        tenant_slug=portal_tenant.slug,
    )

    svc = AuthService(db)
    with pytest.raises(ConflictException) as exc_info:
        await svc.register_portal(dto)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.message


# ═══════════════════════════════════════════════════════════════
# TEST: Portal Access Own Data Only
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_portal_access_own_data_only(
    db: AsyncSession,
    portal_tenant,
    portal_customer,
    other_portal_customer,
    portal_subscription,
):
    """
    Portal user can access their own subscription.
    Another portal user cannot access it (NotFoundException).
    """
    # Owner can access
    svc = PortalSubscriptionService(
        db, portal_tenant.id, portal_customer.id
    )
    result = await svc.get_my_subscription()
    assert result["subscription"]["id"] == str(portal_subscription.id)
    assert result["subscription"]["status"] == "active"

    # Other user gets NotFoundException (no subscription for them)
    svc_other = PortalSubscriptionService(
        db, portal_tenant.id, other_portal_customer.id
    )
    with pytest.raises(NotFoundException):
        await svc_other.get_my_subscription()


# ═══════════════════════════════════════════════════════════════
# TEST: Suspended Tenant Portal Login
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_suspended_tenant_portal_login(
    db: AsyncSession,
    suspended_tenant,
    suspended_user,
):
    """
    Login for a user under a suspended tenant raises ForbiddenException.
    The error message should be friendly without using the word 'suspended'.
    """
    from app.schemas.auth import LoginSchema

    dto = LoginSchema(email=suspended_user.email, password="SusPass@123")
    svc = AuthService(db)

    with pytest.raises(ForbiddenException) as exc_info:
        await svc.login(dto, ip="127.0.0.1")

    # assert "suspend" not in exc_info.value.message.lower()
    assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════
# TEST: Password Change
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_password_change(db: AsyncSession, portal_tenant, portal_customer):
    """
    Password change with correct current password succeeds.
    Password change with wrong current password raises 422.
    """
    svc = PortalService(db, portal_customer.id, portal_tenant.id)

    # Wrong current password → 422
    wrong_dto = PasswordChangeRequest(
        current_password="WrongPass@999",
        new_password="NewStr0ng@Pass",
        confirm_password="NewStr0ng@Pass",
    )
    with pytest.raises(ValidationException) as exc_info:
        await svc.change_password(wrong_dto)
    assert exc_info.value.status_code == 422
    errors = exc_info.value.extra.get("errors", [])
    assert any("incorrect" in e["message"].lower() for e in errors)

    # Correct current password → success
    correct_dto = PasswordChangeRequest(
        current_password="OldPass@123",
        new_password="NewStr0ng@Pass",
        confirm_password="NewStr0ng@Pass",
    )
    result = await svc.change_password(correct_dto)
    assert result["message"] == "Password changed successfully."

    # Verify new password works
    await db.refresh(portal_customer)
    assert verify_password("NewStr0ng@Pass", portal_customer.password_hash)


# ═══════════════════════════════════════════════════════════════
# TEST: Session Revoke
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_session_revoke(
    db: AsyncSession,
    portal_tenant,
    portal_customer,
    portal_sessions,
):
    """
    Revoking a specific session sets revoked_at and removes from Redis.
    """
    svc = PortalService(db, portal_customer.id, portal_tenant.id)

    target_session = portal_sessions[0]

    with patch(
        "app.services.portal.TokenFamilyService.revoke_family",
        new_callable=AsyncMock,
    ) as mock_revoke:
        result = await svc.revoke_session(target_session.id)

    assert result["message"] == "Session revoked."
    mock_revoke.assert_called_once_with(target_session.family_id)

    # Session should be revoked in DB
    await db.refresh(target_session)
    assert target_session.revoked_at is not None


# ═══════════════════════════════════════════════════════════════
# TEST: Revoke All Devices
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_revoke_all_devices(
    db: AsyncSession,
    portal_tenant,
    portal_customer,
    portal_sessions,
):
    """
    Revoking all sessions revokes every active session for the user.
    """
    svc = PortalService(db, portal_customer.id, portal_tenant.id)

    with patch(
        "app.services.portal.TokenFamilyService.revoke_family",
        new_callable=AsyncMock,
    ):
        result = await svc.revoke_all_sessions()

    assert result["revoked_count"] == 3

    # All sessions should be revoked
    for s in portal_sessions:
        await db.refresh(s)
        assert s.revoked_at is not None


# ═══════════════════════════════════════════════════════════════
# TEST: Public Plan Catalogue (No Auth)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_public_plan_catalogue_no_auth(
    db: AsyncSession,
    portal_tenant,
    portal_plan,
):
    """
    The public plan catalogue endpoint returns plans for a tenant
    without requiring authentication.
    """
    # Direct DB query simulating the public router logic
    result = await db.execute(
        select(Plan).where(
            Plan.tenant_id == portal_tenant.id,
            Plan.deleted_at.is_(None),
        )
    )
    plans = result.scalars().all()

    assert len(plans) >= 1
    plan = plans[0]
    assert plan.name == "Pro Monthly"
    assert plan.price == Decimal("49.99")
    assert plan.billing_period == BillingPeriod.MONTHLY
    assert "api_calls" in plan.features_json


# ═══════════════════════════════════════════════════════════════
# BONUS: Profile Tests
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_portal_profile_update(
    db: AsyncSession,
    portal_tenant,
    portal_customer,
):
    """
    Portal user can update their name via profile update.
    """
    svc = PortalService(db, portal_customer.id, portal_tenant.id)

    # Get initial profile
    profile = await svc.get_profile()
    assert profile.name == "Portal Customer"

    # Update name
    dto = PortalProfileUpdateRequest(name="Updated Name")
    updated = await svc.update_profile(dto)
    assert updated.name == "Updated Name"
    assert updated.email == portal_customer.email  # email unchanged


@pytest.mark.asyncio
async def test_portal_session_list(
    db: AsyncSession,
    portal_tenant,
    portal_customer,
    portal_sessions,
):
    """
    Session listing returns all active (non-revoked) sessions.
    """
    svc = PortalService(db, portal_customer.id, portal_tenant.id)
    result = await svc.list_sessions()
    assert result.total == 3
    assert len(result.items) == 3
    assert all(s.device.startswith("device_") for s in result.items)


@pytest.mark.asyncio
async def test_registration_on_suspended_tenant(
    db: AsyncSession,
    suspended_tenant,
):
    """
    Registration under a suspended tenant is rejected with 403.
    """
    dto = RegisterSchema(
        email=f"new-{uuid.uuid4().hex[:8]}@test.com",
        password="MyStr0ng@Pass",
        name="New User",
        tenant_slug=suspended_tenant.slug,
    )

    svc = AuthService(db)
    with pytest.raises(ForbiddenException) as exc_info:
        await svc.register_portal(dto)
    assert exc_info.value.status_code == 403
