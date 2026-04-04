"""
Company audit service — tenant-scoped audit log queries + CSV export.

Scoped to the company's own tenant_id — only sees their own audit trail.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.advanced import (
    CompanyAuditLogFilter,
    CompanyAuditLogItem,
    CompanyAuditLogResponse,
)
from app.services.base import BaseService


class CompanyAuditService(BaseService):
    """Tenant-scoped audit log access."""

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(db)
        self.tenant_id = tenant_id

    async def list_audit_logs(
        self, filters: CompanyAuditLogFilter
    ) -> CompanyAuditLogResponse:
        """Filtered + paginated audit log for this tenant."""
        offset = (filters.page - 1) * filters.page_size

        base = and_(
            AuditLog.tenant_id == self.tenant_id,
            AuditLog.deleted_at.is_(None),
        )

        # Build filter conditions
        conditions = [base]
        if filters.entity_type:
            conditions.append(AuditLog.entity_type == filters.entity_type)
        if filters.action:
            conditions.append(AuditLog.action == filters.action)
        if filters.date_from:
            conditions.append(AuditLog.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(AuditLog.created_at <= filters.date_to)

        combined = and_(*conditions)

        # Count
        count_q = (
            select(func.count())
            .select_from(AuditLog)
            .where(combined)
        )
        total = (await self.db.execute(count_q)).scalar_one()

        # Items
        query = (
            select(AuditLog)
            .where(combined)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(query)
        entries = result.scalars().all()

        items: list[CompanyAuditLogItem] = []
        for entry in entries:
            actor = await self._get_user(entry.actor_id)
            items.append(
                CompanyAuditLogItem(
                    id=entry.id,
                    actor_id=entry.actor_id,
                    actor_name=actor.name if actor else None,
                    actor_role=entry.actor_role.value,
                    entity_type=entry.entity_type,
                    entity_id=entry.entity_id,
                    action=entry.action,
                    diff_json=entry.diff_json or {},
                    created_at=entry.created_at,
                )
            )

        return CompanyAuditLogResponse(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    async def export_csv(
        self, filters: CompanyAuditLogFilter
    ) -> str:
        """Generate CSV of audit log."""
        filters.page = 1
        filters.page_size = 10000

        response = await self.list_audit_logs(filters)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Timestamp", "Actor", "Role",
            "Entity Type", "Entity ID", "Action", "Changes",
        ])

        for item in response.items:
            writer.writerow([
                str(item.id),
                item.created_at.isoformat() if item.created_at else "",
                item.actor_name or "",
                item.actor_role,
                item.entity_type,
                str(item.entity_id),
                item.action.value if item.action else "",
                str(item.diff_json),
            ])

        return output.getvalue()

    async def _get_user(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
