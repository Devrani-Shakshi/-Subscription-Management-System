"""
All application-wide enumerations — single source of truth.
Used consistently across SQLAlchemy models, Pydantic schemas, and service logic.
"""

import enum


# ── User Roles ───────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    COMPANY = "company"
    PORTAL_USER = "portal_user"


# ── Tenant Status ────────────────────────────────────────────────
class TenantStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"


# ── Billing ──────────────────────────────────────────────────────
class BillingPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


# ── Subscription ─────────────────────────────────────────────────
class SubscriptionStatus(str, enum.Enum):
    DRAFT = "draft"
    QUOTATION = "quotation"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


# ── Invoice ──────────────────────────────────────────────────────
class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


# ── Payment ──────────────────────────────────────────────────────
class PaymentMethod(str, enum.Enum):
    CARD = "card"
    BANK = "bank"
    CASH = "cash"
    OTHER = "other"


# ── Discount ─────────────────────────────────────────────────────
class DiscountType(str, enum.Enum):
    FIXED = "fixed"
    PERCENT = "percent"


class DiscountAppliesTo(str, enum.Enum):
    PRODUCT = "product"
    SUBSCRIPTION = "subscription"


# ── Audit ────────────────────────────────────────────────────────
class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    STATUS_CHANGE = "status_change"


# ── Dunning ──────────────────────────────────────────────────────
class DunningStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class DunningAction(str, enum.Enum):
    RETRY = "retry"
    SUSPEND = "suspend"
    CANCEL = "cancel"


# ── Bulk Operations ──────────────────────────────────────────────
class BulkOperationType(str, enum.Enum):
    ACTIVATE = "activate"
    CLOSE = "close"
    APPLY_DISCOUNT = "apply_discount"
    CHANGE_PLAN = "change_plan"


class BulkJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Churn ────────────────────────────────────────────────────────
class ChurnRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Revenue Recognition ─────────────────────────────────────────
class RecognitionType(str, enum.Enum):
    RATABLE = "ratable"
    MILESTONE = "milestone"
