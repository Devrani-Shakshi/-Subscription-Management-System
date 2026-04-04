"""
Super-admin audit service — cross-tenant audit log access + CSV export.

Provides:
- Filtered/paginated audit log listing
- CSV export generation
- User enrichment (actor names/emails from User table)
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.admin import AuditLogRepository, TenantRepository
from app.schemas.admin import (
    AuditLogFilter,
    AuditLogItem,
    AuditLogResponse,
)
from app.services.base import BaseService


class SuperAdminAuditService(BaseService):
    """Cross-tenant audit log queries and export."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._audit_repo = AuditLogRepository(db)
        self._tenants = TenantRepository(db)

    # ── LIST (filtered + paginated) ──────────────────────────────
    async def list_audit_logs(
        self, filters: AuditLogFilter
    ) -> AuditLogResponse:
        """
        Retrieve audit logs with optional filters.

        Enriches each entry with actor name/email and tenant name.
        """
        offset = (filters.page - 1) * filters.page_size

        entries, total = await self._audit_repo.list_filtered(
            tenant_id=filters.tenant_id,
            actor_id=filters.actor_id,
            entity_type=filters.entity_type,
            action=filters.action.value if filters.action else None,
            date_from=filters.date_from,
            date_to=filters.date_to,
            offset=offset,
            limit=filters.page_size,
        )

        items: list[AuditLogItem] = []
        for entry in entries:
            actor = await self._get_user_safe(entry.actor_id)
            tenant_name = await self._get_tenant_name(entry.tenant_id)

            items.append(
                AuditLogItem(
                    id=entry.id,
                    tenant_id=entry.tenant_id,
                    tenant_name=tenant_name,
                    actor_id=entry.actor_id,
                    actor_email=actor.email if actor else None,
                    actor_name=actor.name if actor else None,
                    actor_role=entry.actor_role.value,
                    entity_type=entry.entity_type,
                    entity_id=entry.entity_id,
                    action=entry.action,
                    diff_json=entry.diff_json or {},
                    created_at=entry.created_at,
                )
            )

        return AuditLogResponse(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    # ── CSV EXPORT ───────────────────────────────────────────────
    async def export_csv(
        self, filters: AuditLogFilter
    ) -> str:
        """
        Generate CSV string of audit log data.

        Overrides page_size to fetch all matching rows (capped at 10k).
        """
        filters.page = 1
        filters.page_size = 10000

        response = await self.list_audit_logs(filters)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Timestamp", "Tenant", "Actor Email",
            "Actor Name", "Actor Role", "Entity Type",
            "Entity ID", "Action", "Changes",
        ])

        for item in response.items:
            writer.writerow([
                str(item.id),
                item.created_at.isoformat() if item.created_at else "",
                item.tenant_name or "",
                item.actor_email or "",
                item.actor_name or "",
                item.actor_role,
                item.entity_type,
                str(item.entity_id),
                item.action.value if item.action else "",
                str(item.diff_json),
            ])

        return output.getvalue()

    # ═════════════════════════════════════════════════════════════
    # Private helpers
    # ═════════════════════════════════════════════════════════════

    async def _get_user_safe(self, user_id: uuid.UUID) -> User | None:
        """Lookup user by ID, return None if not found."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_tenant_name(
        self, tenant_id: uuid.UUID | None
    ) -> str | None:
        """Lookup tenant name by ID, return None if not found."""
        if tenant_id is None:
            return None
        result = await self.db.execute(
            select(Tenant.name).where(Tenant.id == tenant_id)
        )
        row = result.scalar_one_or_none()
        return row if row else None
