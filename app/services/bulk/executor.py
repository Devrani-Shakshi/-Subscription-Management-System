"""
Bulk executor — orchestrates conflict detection + batch execution.

Handles:
  1. Conflict detection (pre-flight)
  2. Filtering out skipped items
  3. Batch execution with rollback on failure
  4. Result aggregation
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BulkOperationType
from app.services.bulk.conflict_detector import ConflictDetector
from app.services.bulk.factory import BulkOperationFactory
from app.services.bulk.operations import BulkResult

logger = logging.getLogger(__name__)

# Maximum batch size for execution
_BATCH_SIZE = 50


class BulkExecutor:
    """
    Orchestrates bulk operation execution.

    Flow:
    1. Run ConflictDetector to find all conflicts.
    2. Filter out conflicting IDs (or ones user chose to skip).
    3. Execute in batches of 50.
    4. Aggregate results.
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def preview(
        self,
        ids: list[uuid.UUID],
        operation_type: BulkOperationType | str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Preview conflicts before execution.

        Returns conflict report for UI to display.
        """
        report = await ConflictDetector.detect(
            ids=ids,
            operation_type=operation_type,
            db=self.db,
            tenant_id=self.tenant_id,
            params=params,
        )
        conflict_ids = {c.id for c in report.conflicts}
        clean_ids = [i for i in ids if i not in conflict_ids]

        return {
            "total": len(ids),
            "clean_count": len(clean_ids),
            "conflict_count": len(report.conflicts),
            "conflicts": [
                {
                    "id": str(c.id),
                    "conflict_type": c.conflict_type,
                    "reason": c.reason,
                }
                for c in report.conflicts
            ],
        }

    async def run(
        self,
        ids: list[uuid.UUID],
        operation_type: BulkOperationType | str,
        params: dict[str, Any] | None = None,
        skip_ids: list[uuid.UUID] | None = None,
    ) -> BulkResult:
        """
        Execute the bulk operation.

        Parameters
        ----------
        ids : All subscription IDs to process.
        operation_type : The operation to perform.
        params : Extra params (discount_id, plan_id, etc.).
        skip_ids : IDs to skip (from conflict resolution UI).
        """
        skip_set = set(skip_ids or [])
        execute_ids = [i for i in ids if i not in skip_set]

        if not execute_ids:
            return BulkResult(total=0)

        operation = BulkOperationFactory.create(
            op_type=operation_type,
            db=self.db,
            tenant_id=self.tenant_id,
            params=params,
        )

        # Execute in batches
        final_result = BulkResult(total=len(execute_ids))

        for i in range(0, len(execute_ids), _BATCH_SIZE):
            batch = execute_ids[i : i + _BATCH_SIZE]
            try:
                batch_result = await operation.execute(batch)
                final_result.success.extend(batch_result.success)
                final_result.failed.extend(batch_result.failed)
            except Exception as e:
                logger.error(
                    "Batch %d-%d failed: %s", i, i + len(batch), e
                )
                # Mark entire batch as failed on exception
                for bid in batch:
                    if bid not in final_result.success:
                        from app.services.bulk.operations import FailedItem
                        final_result.failed.append(
                            FailedItem(id=bid, reason=str(e))
                        )

        return final_result
