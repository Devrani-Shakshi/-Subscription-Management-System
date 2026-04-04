"""
Audit logger utility — structured audit trail helper.

Provides a clean interface for creating AuditLog entries from services.
Decouples audit creation from business logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditAction, UserRole
from app.models.audit_log import AuditLog
from app.models.session import Session as SessionModel


class AuditLogger:
    """Factory for creating audit log entries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        *,
        actor_id: uuid.UUID,
        actor_role: UserRole,
        tenant_id: uuid.UUID | None,
        entity_type: str,
        entity_id: uuid.UUID,
        action: AuditAction,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        session_id: uuid.UUID | None = None,
    ) -> AuditLog:
        """
        Create an immutable audit log entry.

        Parameters
        ----------
        actor_id : UUID of the user performing the action.
        actor_role : Role of the actor.
        tenant_id : Tenant scope (None for super_admin actions).
        entity_type : e.g. 'tenant', 'user', 'subscription'.
        entity_id : UUID of the affected entity.
        action : The AuditAction enum value.
        before : State before the change (for diffs).
        after : State after the change (for diffs).
        session_id : Session UUID. If not provided, a system
                     session placeholder is created.
        """
        diff: dict[str, Any] = {}
        if before is not None:
            diff["before"] = before
        if after is not None:
            diff["after"] = after

        # If no session_id provided, create a system placeholder session
        if session_id is None:
            session_id = await self._get_or_create_system_session(
                actor_id, tenant_id
            )

        entry = AuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_role=actor_role,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            diff_json=diff,
            session_id=session_id,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def _get_or_create_system_session(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID | None,
    ) -> uuid.UUID:
        """
        Create a lightweight system session for audit purposes.

        This ensures FK integrity for audit_log.session_id → sessions.id.
        """
        session = SessionModel(
            user_id=user_id,
            tenant_id=tenant_id,
            refresh_token_hash="system-audit-placeholder",
            family_id=uuid.uuid4(),
            device_fingerprint="system",
            ip_subnet="0.0.0.0",
            expires_at=datetime.utcnow() + timedelta(minutes=1),
        )
        self.db.add(session)
        await self.db.flush()
        return session.id
