"""
Pytest fixtures for database testing.

Uses SQLite with type-compilation adapters for PG-specific types.
RLS tests require a real PostgreSQL database.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import date
from decimal import Decimal
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import String, Text, event, create_engine
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.enums import BillingPeriod, TenantStatus, UserRole
from app.models.base import BaseModel

# Force all models into metadata
from app.models import (  # noqa: F401
    Tenant,
    User,
    Session,
    Product,
    Plan,
    Subscription,
    Invoice,
)


# ═══════════════════════════════════════════════════════════════
# Patch PG types for SQLite DDL compatibility
# ═══════════════════════════════════════════════════════════════

def _patch_pg_types_for_sqlite():
    """
    Monkey-patch PostgreSQL type visit methods on the SQLite compiler
    so that create_all works on SQLite.
    """
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    # UUID → CHAR(36)
    if not hasattr(SQLiteTypeCompiler, "visit_UUID"):
        SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "CHAR(36)"

    # JSONB → TEXT
    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
        SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "TEXT"

    # ARRAY → TEXT  (stored as JSON-encoded string)
    if not hasattr(SQLiteTypeCompiler, "visit_ARRAY"):
        SQLiteTypeCompiler.visit_ARRAY = lambda self, type_, **kw: "TEXT"


_patch_pg_types_for_sqlite()


# ── Async event-loop ────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Engine + tables ─────────────────────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    @event.listens_for(eng.sync_engine, "connect")
    def _enable_fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    async with eng.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        async with session.begin():
            yield session
        await session.rollback()


# ═══════════════════════════════════════════════════════════════
# Seed Data Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def tenant(db: AsyncSession):
    from app.models.tenant import Tenant

    t = Tenant(
        id=uuid.uuid4(),
        name="Acme Corp",
        slug=f"acme-corp-{uuid.uuid4().hex[:8]}",
        status=TenantStatus.ACTIVE,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def company_user(db: AsyncSession, tenant):
    from app.models.user import User

    u = User(
        id=uuid.uuid4(),
        email=f"admin-{uuid.uuid4().hex[:8]}@acme.test",
        password_hash="hashed_pw",
        role=UserRole.COMPANY,
        tenant_id=tenant.id,
        name="Acme Admin",
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def portal_user(db: AsyncSession, tenant):
    from app.models.user import User

    u = User(
        id=uuid.uuid4(),
        email=f"customer-{uuid.uuid4().hex[:8]}@example.test",
        password_hash="hashed_pw",
        role=UserRole.PORTAL_USER,
        tenant_id=tenant.id,
        name="Test Customer",
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def super_admin(db: AsyncSession):
    from app.models.user import User

    u = User(
        id=uuid.uuid4(),
        email=f"superadmin-{uuid.uuid4().hex[:8]}@platform.test",
        password_hash="hashed_pw",
        role=UserRole.SUPER_ADMIN,
        tenant_id=None,
        name="Platform Admin",
    )
    db.add(u)
    await db.flush()
    return u


@pytest_asyncio.fixture
async def product(db: AsyncSession, tenant):
    from app.models.product import Product

    p = Product(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Widget Pro",
        type="physical",
        sales_price=Decimal("49.99"),
        cost_price=Decimal("20.00"),
    )
    db.add(p)
    await db.flush()
    return p


@pytest_asyncio.fixture
async def plan(db: AsyncSession, tenant):
    from app.models.plan import Plan

    pl = Plan(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Monthly Basic",
        price=Decimal("29.99"),
        billing_period=BillingPeriod.MONTHLY,
        min_qty=1,
        start_date=date(2026, 1, 1),
        end_date=None,
        features_json={"max_users": 5, "storage_gb": 10},
        flags_json={
            "auto_close": False,
            "closable": True,
            "pausable": False,
            "renewable": True,
        },
    )
    db.add(pl)
    await db.flush()
    return pl
