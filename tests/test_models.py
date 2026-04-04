"""
Tests for SQLAlchemy models — creation, soft-delete, to_dict, and
relationship integrity.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TenantStatus, UserRole
from app.models.tenant import Tenant
from app.models.user import User


@pytest.mark.asyncio
class TestTenantModel:
    async def test_create_tenant(self, db: AsyncSession, tenant: Tenant):
        assert tenant.id is not None
        assert tenant.slug.startswith("acme-corp")
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.deleted_at is None

    async def test_soft_delete_tenant(self, db: AsyncSession, tenant: Tenant):
        tenant.soft_delete()
        await db.flush()
        assert tenant.deleted_at is not None

    async def test_restore_tenant(self, db: AsyncSession, tenant: Tenant):
        tenant.soft_delete()
        await db.flush()
        tenant.restore()
        await db.flush()
        assert tenant.deleted_at is None

    async def test_to_dict_strip_sensitive(
        self, db: AsyncSession, tenant: Tenant
    ):
        d = tenant.to_dict()
        assert "id" in d
        assert "name" in d
        assert "password_hash" not in d


@pytest.mark.asyncio
class TestUserModel:
    async def test_create_user(
        self, db: AsyncSession, company_user: User
    ):
        assert company_user.role == UserRole.COMPANY
        assert company_user.tenant_id is not None

    async def test_super_admin_no_tenant(
        self, db: AsyncSession, super_admin: User
    ):
        assert super_admin.role == UserRole.SUPER_ADMIN
        assert super_admin.tenant_id is None

    async def test_to_dict_strips_password(
        self, db: AsyncSession, company_user: User
    ):
        d = company_user.to_dict()
        assert "password_hash" not in d
        assert "email" in d
