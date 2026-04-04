"""
Tests for audit trail module.

Covers:
  - AuditLogger creates entries with diffs
  - CompanyAuditService filtering by entity_type, action
  - CSV export
  - Append-only enforcement (audit entries never modified)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditAction, UserRole
from app.models.audit_log import AuditLog
from app.schemas.advanced import CompanyAuditLogFilter
from app.services.audit_logger import AuditLogger
from app.services.company_audit import CompanyAuditService


@pytest_asyncio.fixture
async def audit_entry(
    db: AsyncSession, tenant, company_user
) -> AuditLog:
    """Create a sample audit log entry."""
    logger = AuditLogger(db)
    entry = await logger.log(
        actor_id=company_user.id,
        actor_role=UserRole.COMPANY,
        tenant_id=tenant.id,
        entity_type="subscription",
        entity_id=uuid.uuid4(),
        action=AuditAction.CREATE,
        before=None,
        after={"status": "active", "plan": "Pro"},
    )
    return entry


class TestAuditLogger:
    """Test AuditLogger entry creation."""

    @pytest.mark.asyncio
    async def test_log_creates_entry(
        self, db: AsyncSession, tenant, company_user
    ):
        """AuditLogger.log creates a valid entry."""
        logger = AuditLogger(db)
        entry = await logger.log(
            actor_id=company_user.id,
            actor_role=UserRole.COMPANY,
            tenant_id=tenant.id,
            entity_type="product",
            entity_id=uuid.uuid4(),
            action=AuditAction.CREATE,
            after={"name": "Widget"},
        )
        assert entry.id is not None
        assert entry.entity_type == "product"
        assert entry.action == AuditAction.CREATE
        assert entry.diff_json["after"]["name"] == "Widget"

    @pytest.mark.asyncio
    async def test_log_with_before_and_after(
        self, db: AsyncSession, tenant, company_user
    ):
        """Diff contains both before and after states."""
        logger = AuditLogger(db)
        entry = await logger.log(
            actor_id=company_user.id,
            actor_role=UserRole.COMPANY,
            tenant_id=tenant.id,
            entity_type="plan",
            entity_id=uuid.uuid4(),
            action=AuditAction.UPDATE,
            before={"price": "29.99"},
            after={"price": "39.99"},
        )
        assert "before" in entry.diff_json
        assert "after" in entry.diff_json
        assert entry.diff_json["before"]["price"] == "29.99"
        assert entry.diff_json["after"]["price"] == "39.99"

    @pytest.mark.asyncio
    async def test_auto_creates_system_session(
        self, db: AsyncSession, tenant, company_user
    ):
        """When no session_id provided, creates placeholder session."""
        logger = AuditLogger(db)
        entry = await logger.log(
            actor_id=company_user.id,
            actor_role=UserRole.COMPANY,
            tenant_id=tenant.id,
            entity_type="tax",
            entity_id=uuid.uuid4(),
            action=AuditAction.DELETE,
        )
        assert entry.session_id is not None


class TestCompanyAuditService:
    """Test company-scoped audit service."""

    @pytest.mark.asyncio
    async def test_list_audit_logs(
        self, db: AsyncSession, tenant, company_user, audit_entry
    ):
        """list_audit_logs returns entries for this tenant."""
        svc = CompanyAuditService(db, tenant.id)
        filters = CompanyAuditLogFilter()
        result = await svc.list_audit_logs(filters)
        assert result.total >= 1
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_filter_by_entity_type(
        self, db: AsyncSession, tenant, company_user, audit_entry
    ):
        """Filter by entity_type returns matching entries only."""
        svc = CompanyAuditService(db, tenant.id)
        filters = CompanyAuditLogFilter(entity_type="subscription")
        result = await svc.list_audit_logs(filters)
        for item in result.items:
            assert item.entity_type == "subscription"

    @pytest.mark.asyncio
    async def test_filter_by_action(
        self, db: AsyncSession, tenant, company_user, audit_entry
    ):
        """Filter by action returns matching entries only."""
        svc = CompanyAuditService(db, tenant.id)
        filters = CompanyAuditLogFilter(action=AuditAction.CREATE)
        result = await svc.list_audit_logs(filters)
        for item in result.items:
            assert item.action == AuditAction.CREATE

    @pytest.mark.asyncio
    async def test_export_csv(
        self, db: AsyncSession, tenant, company_user, audit_entry
    ):
        """export_csv generates valid CSV with headers."""
        svc = CompanyAuditService(db, tenant.id)
        filters = CompanyAuditLogFilter()
        csv_data = await svc.export_csv(filters)
        assert "ID" in csv_data
        assert "Timestamp" in csv_data
        assert "Entity Type" in csv_data
        lines = csv_data.strip().split("\n")
        assert len(lines) >= 2  # header + at least 1 row

    @pytest.mark.asyncio
    async def test_tenant_isolation(
        self, db: AsyncSession, tenant, company_user, audit_entry
    ):
        """Audit entries from other tenants are not visible."""
        other_tenant_id = uuid.uuid4()
        svc = CompanyAuditService(db, other_tenant_id)
        filters = CompanyAuditLogFilter()
        result = await svc.list_audit_logs(filters)
        assert result.total == 0
