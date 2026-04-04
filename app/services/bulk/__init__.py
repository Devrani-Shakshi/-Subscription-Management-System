"""
Bulk operations — abstract operations + conflict detection + executor.

Classes:
    BulkOperation (ABC)      — validate + execute interface
    BulkActivate             — bulk activate subscriptions
    BulkClose                — bulk close subscriptions
    BulkApplyDiscount        — bulk apply discount
    BulkChangePlan           — bulk change plan
    BulkOperationFactory     — factory for creating operations
    ConflictDetector         — pre-flight conflict checks
    BulkExecutor             — orchestrates conflict check + batch execution
"""

from app.services.bulk.operations import (
    BulkOperation,
    BulkResult,
    ConflictItem,
    ConflictReport,
    FailedItem,
    BulkActivate,
    BulkClose,
    BulkApplyDiscount,
    BulkChangePlan,
)
from app.services.bulk.factory import BulkOperationFactory
from app.services.bulk.conflict_detector import ConflictDetector
from app.services.bulk.executor import BulkExecutor

__all__ = [
    "BulkOperation",
    "BulkResult",
    "ConflictItem",
    "ConflictReport",
    "FailedItem",
    "BulkActivate",
    "BulkClose",
    "BulkApplyDiscount",
    "BulkChangePlan",
    "BulkOperationFactory",
    "ConflictDetector",
    "BulkExecutor",
]
