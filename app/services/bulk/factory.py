"""
Bulk operation factory — maps operation type string to concrete class.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BulkOperationType
from app.exceptions.base import ValidationException
from app.services.bulk.operations import (
    BulkActivate,
    BulkApplyDiscount,
    BulkChangePlan,
    BulkClose,
    BulkOperation,
)

_REGISTRY: dict[BulkOperationType, type[BulkOperation]] = {
    BulkOperationType.ACTIVATE: BulkActivate,
    BulkOperationType.CLOSE: BulkClose,
    BulkOperationType.APPLY_DISCOUNT: BulkApplyDiscount,
    BulkOperationType.CHANGE_PLAN: BulkChangePlan,
}


class BulkOperationFactory:
    """Factory for creating bulk operation instances."""

    @staticmethod
    def create(
        op_type: BulkOperationType | str,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        params: dict[str, Any] | None = None,
    ) -> BulkOperation:
        """
        Create a bulk operation instance.

        Parameters
        ----------
        op_type : Operation type (enum or string value).
        db : Database session.
        tenant_id : Tenant UUID.
        params : Extra params (e.g. discount_id, plan_id).

        Raises
        ------
        ValidationException
            If op_type is not recognized.
        """
        if isinstance(op_type, str):
            try:
                op_type = BulkOperationType(op_type)
            except ValueError:
                raise ValidationException(
                    errors=[
                        {
                            "field": "operation",
                            "message": (
                                f"Unknown operation: {op_type}. "
                                f"Valid: {[e.value for e in BulkOperationType]}"
                            ),
                        }
                    ]
                )

        cls = _REGISTRY.get(op_type)
        if cls is None:
            raise ValidationException(
                errors=[
                    {
                        "field": "operation",
                        "message": f"No handler for {op_type.value}.",
                    }
                ]
            )

        return cls(db=db, tenant_id=tenant_id, params=params)
