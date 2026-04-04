"""
Conflict detector — pure class that checks ALL conflicts before execution.

Delegates to the operation's validate() method but provides a unified
interface for the executor to call.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BulkOperationType
from app.services.bulk.factory import BulkOperationFactory
from app.services.bulk.operations import ConflictReport


class ConflictDetector:
    """
    Pre-flight conflict detector.

    Checks ALL conflicts before any execution begins.
    This is a pure validation class — no side effects.
    """

    @staticmethod
    async def detect(
        ids: list[uuid.UUID],
        operation_type: BulkOperationType | str,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        params: dict[str, Any] | None = None,
    ) -> ConflictReport:
        """
        Detect all conflicts for the given operation.

        Returns a ConflictReport with all detected issues.
        """
        operation = BulkOperationFactory.create(
            op_type=operation_type,
            db=db,
            tenant_id=tenant_id,
            params=params,
        )
        return await operation.validate(ids)
