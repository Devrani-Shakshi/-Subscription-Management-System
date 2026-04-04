"""
Auth integration tests — cover all flows specified in the spec.

Uses FastAPI dependency_overrides for DB mocking (the correct approach).
Redis is mocked globally via autouse fixture.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password, hash_token, generate_invite_token
from app.core.enums import TenantStatus, UserRole
from app.dependencies.db import get_db_no_tenant
from app.main import app


# ═══════════════════════════════════════════════════════════════
# Mock Redis — all tests run without a real Redis
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis for all tests — no real Redis needed."""
    mock = AsyncMock()
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock()
    mock.ttl = AsyncMock(return_value=600)
    mock.sadd = AsyncMock()
    mock.srem = AsyncMock(return_value=1)
    mock.delete = AsyncMock()

    with patch("app.core.redis.get_redis", return_value=mock):
        with patch("app.services.rate_limit.get_redis", return_value=mock):
            with patch("app.services.token_family.get_redis", return_value=mock):
                yield mock


# ═══════════════════════════════════════════════════════════════
# DB mock helper — proper FastAPI dependency override
# ═══════════════════════════════════════════════════════════════

def _mock_db_override(execute_side_effect=None, execute_return=None):
    """Create a DB override for FastAPI dependency injection."""
    async def override():
        db = AsyncMock()
        if execute_side_effect:
            db.execute = AsyncMock(side_effect=execute_side_effect)
        elif execute_return is not None:
            db.execute = AsyncMock(return_value=execute_return)
        else:
            db.execute = AsyncMock()
        db.add = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.close = AsyncMock()
        yield db

    return override


# ═══════════════════════════════════════════════════════════════
# Model factories — use real-looking email domains
# ═══════════════════════════════════════════════════════════════

def _make_user(
    *,
    email: str = "test@example.com",
    password: str = "Test@1234",
    role: UserRole = UserRole.COMPANY,
    tenant_id: uuid.UUID | None = None,
    name: str = "Test User",
):
    from app.models.user import User
    return User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        role=role,
        tenant_id=tenant_id,
        name=name,
    )


def _make_tenant(
    *,
    slug: str = "acme",
    status: TenantStatus = TenantStatus.ACTIVE,
):
    from app.models.tenant import Tenant
    return Tenant(
        id=uuid.uuid4(),
        name="Acme Corp",
        slug=slug,
        status=status,
    )


def _mock_result(value):
    """Create a mock DB execute result."""
    r = AsyncMock()
    r.scalar_one_or_none = lambda: value
    return r


# ═══════════════════════════════════════════════════════════════
# Client fixture
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════

class TestSeedSuperAdmin:
    """POST /auth/seed — bootstrap super_admin."""

    @pytest.mark.asyncio
    async def test_seed_success(self, client, mock_redis):
        """Seed creates super_admin with correct secret."""
        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_return=_mock_result(None)
        )

        resp = await client.post(
            "/auth/seed",
            json={
                "email": "admin@platform.io",
                "password": "SuperAdmin@1234",
                "name": "Platform Admin",
            },
            headers={"x-seed-secret": "CHANGE-ME-seed-secret"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "admin@platform.io"
        assert data["role"] == "super_admin"

    @pytest.mark.asyncio
    async def test_seed_wrong_secret(self, client):
        """Seed with wrong secret → 403."""
        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_return=_mock_result(None)
        )

        resp = await client.post(
            "/auth/seed",
            json={
                "email": "admin@platform.io",
                "password": "SuperAdmin@1234",
                "name": "Platform Admin",
            },
            headers={"x-seed-secret": "wrong-secret"},
        )
        assert resp.status_code == 403


class TestLogin:
    """POST /auth/login — authentication."""

    @pytest.mark.asyncio
    async def test_login_success(self, client, mock_redis):
        """Valid credentials → 200 with access_token."""
        password = "Company@1234"
        tenant = _make_tenant()
        user = _make_user(
            email="company@acme.io",
            password=password,
            role=UserRole.COMPANY,
            tenant_id=tenant.id,
        )

        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_result(user)
            return _mock_result(tenant)

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_side_effect=execute_side_effect
        )

        resp = await client.post(
            "/auth/login",
            json={"email": "company@acme.io", "password": password},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "company"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, mock_redis):
        """Wrong password → 401 'Invalid credentials.'"""
        user = _make_user(
            email="company@acme.io",
            password="Company@1234",
            role=UserRole.COMPANY,
        )

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_return=_mock_result(user)
        )

        resp = await client.post(
            "/auth/login",
            json={"email": "company@acme.io", "password": "WrongPass@123"},
        )

        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_login_suspended_tenant(self, client, mock_redis):
        """Suspended tenant → 403."""
        tenant = _make_tenant(status=TenantStatus.SUSPENDED)
        user = _make_user(
            email="company@suspended.io",
            password="Company@1234",
            role=UserRole.COMPANY,
            tenant_id=tenant.id,
        )

        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_result(user)
            return _mock_result(tenant)

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_side_effect=execute_side_effect
        )

        resp = await client.post(
            "/auth/login",
            json={
                "email": "company@suspended.io",
                "password": "Company@1234",
            },
        )

        assert resp.status_code == 403
        assert "suspended" in resp.json()["message"].lower()


class TestInvite:
    """POST /auth/invite/accept — activate invited account."""

    @pytest.mark.asyncio
    async def test_invite_accept_success(self, client, mock_redis):
        """Valid invite → 201 with user info."""
        from app.models.invite_token import InviteToken

        raw_token = generate_invite_token()
        tenant_id = uuid.uuid4()
        invite = InviteToken(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            email="invited@company.io",
            role=UserRole.COMPANY,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
            used_at=None,
        )

        mock_tenant = _make_tenant()

        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_result(invite)
            elif call_count == 2:
                return _mock_result(None)
            return _mock_result(mock_tenant)

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_side_effect=execute_side_effect
        )

        resp = await client.post(
            "/auth/invite/accept",
            json={
                "token": raw_token,
                "password": "NewUser@1234",
                "name": "Invited User",
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "invited@company.io"
        assert data["role"] == "company"

    @pytest.mark.asyncio
    async def test_invite_expired(self, client, mock_redis):
        """Expired invite → 410."""
        from app.models.invite_token import InviteToken

        raw_token = generate_invite_token()
        invite = InviteToken(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="expired@example.com",
            role=UserRole.COMPANY,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used_at=None,
        )

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_return=_mock_result(invite)
        )

        resp = await client.post(
            "/auth/invite/accept",
            json={
                "token": raw_token,
                "password": "NewUser@1234",
                "name": "Late User",
            },
        )

        assert resp.status_code == 410
        assert "expired" in resp.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_invite_reuse(self, client, mock_redis):
        """Already-used invite → 410."""
        from app.models.invite_token import InviteToken

        raw_token = generate_invite_token()
        invite = InviteToken(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="used@example.com",
            role=UserRole.COMPANY,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
            used_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_return=_mock_result(invite)
        )

        resp = await client.post(
            "/auth/invite/accept",
            json={
                "token": raw_token,
                "password": "NewUser@1234",
                "name": "Reuse User",
            },
        )

        assert resp.status_code == 410
        assert "already been used" in resp.json()["message"].lower()


class TestRegisterPortal:
    """POST /auth/register — portal self-registration."""

    @pytest.mark.asyncio
    async def test_register_portal_user(self, client, mock_redis):
        """Self-register under valid tenant → 201."""
        tenant = _make_tenant(slug="acme")

        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_result(tenant)
            return _mock_result(None)

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_side_effect=execute_side_effect
        )

        resp = await client.post(
            "/auth/register",
            json={
                "email": "customer@example.com",
                "password": "Customer@1234",
                "name": "Test Customer",
                "tenant_slug": "acme",
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["role"] == "portal_user"


class TestRoleGuards:
    """Verify role-based access control on protected routers."""

    @pytest.mark.asyncio
    async def test_admin_without_token(self, client):
        """No token → 401 on admin route."""
        resp = await client.post(
            "/admin/companies",
            json={"name": "Test", "slug": "test-co", "email": "t@example.com"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_portal_without_token(self, client):
        """No token → 401 on portal route."""
        resp = await client.get("/portal/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_company_without_token(self, client):
        """No token → 401 on company route."""
        resp = await client.post(
            "/company/customers/invite",
            json={"email": "c@example.com"},
        )
        assert resp.status_code == 401


class TestRateLimit:
    """Test rate limiting on login."""

    @pytest.mark.asyncio
    async def test_rate_limit_login(self, client, mock_redis):
        """Exceeding login rate limit → 429."""
        mock_redis.incr = AsyncMock(return_value=6)
        mock_redis.ttl = AsyncMock(return_value=300)

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_return=_mock_result(None)
        )

        resp = await client.post(
            "/auth/login",
            json={"email": "spam@example.com", "password": "x"},
        )
        assert resp.status_code == 429


class TestLogout:
    """POST /auth/logout — session revocation."""

    @pytest.mark.asyncio
    async def test_logout(self, client, mock_redis):
        """Logout always returns 204."""
        app.dependency_overrides[get_db_no_tenant] = _mock_db_override()

        resp = await client.post("/auth/logout")
        assert resp.status_code == 204


class TestHealthAndPublic:
    """Health check and public routes."""

    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_public_tenant_not_found(self, client, mock_redis):
        """Unknown slug → 404."""
        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_return=_mock_result(None)
        )

        resp = await client.get("/public/tenant/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_public_tenant_found(self, client, mock_redis):
        """Valid slug → 200 with branding info."""
        tenant = _make_tenant(slug="acme")

        app.dependency_overrides[get_db_no_tenant] = _mock_db_override(
            execute_return=_mock_result(tenant)
        )

        resp = await client.get("/public/tenant/acme")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Acme Corp"
        assert data["slug"] == "acme"


class TestValidation:
    """Pydantic schema validation on auth endpoints."""

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        """Weak password → 422."""
        app.dependency_overrides[get_db_no_tenant] = _mock_db_override()

        resp = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "name": "Test User",
                "tenant_slug": "acme",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_name(self, client):
        """Name too short → 422."""
        app.dependency_overrides[get_db_no_tenant] = _mock_db_override()

        resp = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "Strong@1234",
                "name": "X",
                "tenant_slug": "acme",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client):
        """Invalid email → 422."""
        app.dependency_overrides[get_db_no_tenant] = _mock_db_override()

        resp = await client.post(
            "/auth/login",
            json={"email": "not-an-email", "password": "Test@1234"},
        )
        assert resp.status_code == 422
