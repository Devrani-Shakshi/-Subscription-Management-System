"""initial_schema

Full schema creation with:
- All 20 tables
- Composite indexes for hot query paths
- PostgreSQL Row-Level Security policies on every tenant-scoped table
- Append-only trigger on audit_log (prevents UPDATE/DELETE)
- Unique constraint: subscription.number per tenant

Revision ID: 001
Revises: None
Create Date: 2026-04-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Enum types ───────────────────────────────────────────────────
tenant_status = postgresql.ENUM(
    "trial", "active", "suspended", name="tenant_status", create_type=False
)
user_role = postgresql.ENUM(
    "super_admin", "company", "portal_user", name="user_role", create_type=False
)
billing_period = postgresql.ENUM(
    "daily", "weekly", "monthly", "yearly", name="billing_period", create_type=False
)
subscription_status = postgresql.ENUM(
    "draft", "quotation", "confirmed", "active", "closed",
    name="subscription_status", create_type=False,
)
invoice_status = postgresql.ENUM(
    "draft", "confirmed", "paid", name="invoice_status", create_type=False
)
payment_method = postgresql.ENUM(
    "card", "bank", "cash", "other", name="payment_method", create_type=False
)
discount_type = postgresql.ENUM(
    "fixed", "percent", name="discount_type", create_type=False
)
discount_applies_to = postgresql.ENUM(
    "product", "subscription", name="discount_applies_to", create_type=False
)
audit_action = postgresql.ENUM(
    "create", "update", "delete", "status_change",
    name="audit_action", create_type=False,
)
dunning_status = postgresql.ENUM(
    "pending", "success", "failed", "skipped",
    name="dunning_status", create_type=False,
)

# Tables that need RLS policies
_TENANT_SCOPED_TABLES = [
    "products",
    "product_variants",
    "plans",
    "subscriptions",
    "subscription_lines",
    "quotation_templates",
    "invoices",
    "invoice_lines",
    "payments",
    "discounts",
    "taxes",
    "audit_log",
    "churn_scores",
    "dunning_schedules",
    "revenue_recognition",
]


def upgrade() -> None:
    # ── Create enum types ────────────────────────────────────────
    op.execute("CREATE TYPE tenant_status AS ENUM ('trial','active','suspended')")
    op.execute("CREATE TYPE user_role AS ENUM ('super_admin','company','portal_user')")
    op.execute("CREATE TYPE billing_period AS ENUM ('daily','weekly','monthly','yearly')")
    op.execute(
        "CREATE TYPE subscription_status AS ENUM "
        "('draft','quotation','confirmed','active','closed')"
    )
    op.execute("CREATE TYPE invoice_status AS ENUM ('draft','confirmed','paid')")
    op.execute("CREATE TYPE payment_method AS ENUM ('card','bank','cash','other')")
    op.execute("CREATE TYPE discount_type AS ENUM ('fixed','percent')")
    op.execute("CREATE TYPE discount_applies_to AS ENUM ('product','subscription')")
    op.execute(
        "CREATE TYPE audit_action AS ENUM ('create','update','delete','status_change')"
    )
    op.execute("CREATE TYPE dunning_status AS ENUM ('pending','success','failed','skipped')")

    # ══════════════════════════════════════════════════════════════
    # TENANTS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", tenant_status, nullable=False, server_default="trial"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # USERS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Now add the deferred FK from tenants.owner_user_id → users.id
    op.create_foreign_key(
        "fk_tenants_owner_user", "tenants", "users",
        ["owner_user_id"], ["id"],
    )

    # ══════════════════════════════════════════════════════════════
    # SESSIONS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("refresh_token_hash", sa.String(512), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_fingerprint", sa.String(512), nullable=False),
        sa.Column("ip_subnet", sa.String(50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # FAILED LOGIN ATTEMPTS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "failed_login_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("ip", sa.String(50), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # PRODUCTS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("sales_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # PRODUCT VARIANTS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attribute", sa.String(100), nullable=False),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("extra_price", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # PLANS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("billing_period", billing_period, nullable=False),
        sa.Column("min_qty", sa.Integer, nullable=False, server_default="1"),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("features_json", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("flags_json", postgresql.JSONB, nullable=False,
                  server_default='{"auto_close":false,"closable":true,"pausable":false,"renewable":true}'),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # SUBSCRIPTIONS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("number", sa.String(50), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("expiry_date", sa.Date, nullable=False),
        sa.Column("payment_terms", sa.String(100), nullable=False,
                  server_default="net-30"),
        sa.Column("status", subscription_status, nullable=False,
                  server_default="draft"),
        sa.Column("downgrade_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downgrade_to_plan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plans.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Subscription number unique per tenant
        sa.UniqueConstraint("tenant_id", "number", name="uq_subscription_tenant_number"),
    )

    # ══════════════════════════════════════════════════════════════
    # SUBSCRIPTION LINES
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "subscription_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("products.id"), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
                  nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # QUOTATION TEMPLATES
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "quotation_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("validity_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # TAXES  (created before invoices/invoice_lines that FK to it)
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "taxes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # DISCOUNTS (created before invoice_lines that FK to it)
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "discounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", discount_type, nullable=False),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("min_purchase", sa.Numeric(10, 2), nullable=False,
                  server_default="0"),
        sa.Column("min_qty", sa.Integer, nullable=False, server_default="1"),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("usage_limit", sa.Integer, nullable=True),
        sa.Column("used_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("applies_to", discount_applies_to, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # INVOICES
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", invoice_status, nullable=False,
                  server_default="draft"),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False,
                  server_default="0"),
        sa.Column("tax_total", sa.Numeric(10, 2), nullable=False,
                  server_default="0"),
        sa.Column("discount_total", sa.Numeric(10, 2), nullable=False,
                  server_default="0"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False,
                  server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # INVOICE LINES
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "invoice_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("products.id"), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("taxes.id"), nullable=True),
        sa.Column("discount_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("discounts.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # PAYMENTS
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("method", payment_method, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # AUDIT LOG
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("actor_role", user_role, nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("diff_json", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )

    # ══════════════════════════════════════════════════════════════
    # CHURN SCORES
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "churn_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("signals_json", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # DUNNING SCHEDULES
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "dunning_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", dunning_status, nullable=False,
                  server_default="pending"),
        sa.Column("result_json", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # REVENUE RECOGNITION
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "revenue_recognition",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("recognized_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("recognition_date", sa.Date, nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ══════════════════════════════════════════════════════════════
    # INDEXES
    # ══════════════════════════════════════════════════════════════
    op.create_index(
        "ix_users_email", "users", ["email"], unique=True,
    )
    op.create_index(
        "ix_users_tenant_role", "users", ["tenant_id", "role"],
    )
    op.create_index(
        "ix_subscriptions_tenant_status", "subscriptions",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_subscriptions_tenant_customer", "subscriptions",
        ["tenant_id", "customer_id"],
    )
    op.create_index(
        "ix_invoices_tenant_status_due", "invoices",
        ["tenant_id", "status", "due_date"],
    )
    op.create_index(
        "ix_audit_log_tenant_entity", "audit_log",
        ["tenant_id", "entity_type", "entity_id"],
    )
    op.create_index(
        "ix_churn_scores_tenant_score", "churn_scores",
        [sa.text("tenant_id"), sa.text("score DESC")],
    )
    op.create_index(
        "ix_sessions_family_id", "sessions", ["family_id"],
    )
    op.create_index(
        "ix_sessions_user_id", "sessions", ["user_id"],
    )
    op.create_index(
        "ix_failed_login_email", "failed_login_attempts", ["email"],
    )

    # ══════════════════════════════════════════════════════════════
    # ROW-LEVEL SECURITY (RLS) — TENANT ISOLATION
    # ══════════════════════════════════════════════════════════════
    #
    # Strategy:
    #   1. Enable RLS on every tenant-scoped table.
    #   2. Create a tenant_isolation policy: tenant_id must match
    #      the session-scoped GUC `app.tenant_id`.
    #   3. Create a super_admin_bypass policy that allows access
    #      when app.tenant_id = 'SUPER'.
    #   4. FORCE RLS so even table owners are subject to policies.
    #
    # The GUC is set per-request in the DB dependency via
    #   SET LOCAL app.tenant_id = '<uuid>' | 'SUPER'

    for table in _TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

        # Tenant isolation: only rows matching the current tenant
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            FOR ALL
            USING (tenant_id = current_setting('app.tenant_id')::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid)
        """)

        # Super admin bypass: when tenant_id GUC is literal 'SUPER'
        op.execute(f"""
            CREATE POLICY super_admin_bypass_{table} ON {table}
            FOR ALL
            USING (current_setting('app.tenant_id', true) = 'SUPER')
            WITH CHECK (current_setting('app.tenant_id', true) = 'SUPER')
        """)

    # ══════════════════════════════════════════════════════════════
    # AUDIT LOG — APPEND-ONLY TRIGGER
    # ══════════════════════════════════════════════════════════════
    # Prevents any UPDATE or DELETE on audit_log rows.

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only. UPDATE and DELETE are prohibited.';
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_mutation();
    """)


def downgrade() -> None:
    # ── Drop trigger + function ──────────────────────────────────
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_immutable ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation()")

    # ── Drop RLS policies ────────────────────────────────────────
    for table in reversed(_TENANT_SCOPED_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"DROP POLICY IF EXISTS super_admin_bypass_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # ── Drop indexes ─────────────────────────────────────────────
    op.drop_index("ix_failed_login_email", table_name="failed_login_attempts")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_index("ix_sessions_family_id", table_name="sessions")
    op.drop_index("ix_churn_scores_tenant_score", table_name="churn_scores")
    op.drop_index("ix_audit_log_tenant_entity", table_name="audit_log")
    op.drop_index("ix_invoices_tenant_status_due", table_name="invoices")
    op.drop_index("ix_subscriptions_tenant_customer", table_name="subscriptions")
    op.drop_index("ix_subscriptions_tenant_status", table_name="subscriptions")
    op.drop_index("ix_users_tenant_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")

    # ── Drop tables in reverse dependency order ──────────────────
    op.drop_table("revenue_recognition")
    op.drop_table("dunning_schedules")
    op.drop_table("churn_scores")
    op.drop_table("audit_log")
    op.drop_table("payments")
    op.drop_table("invoice_lines")
    op.drop_table("invoices")
    op.drop_table("discounts")
    op.drop_table("taxes")
    op.drop_table("quotation_templates")
    op.drop_table("subscription_lines")
    op.drop_table("subscriptions")
    op.drop_table("product_variants")
    op.drop_table("products")
    op.drop_table("failed_login_attempts")
    op.drop_table("sessions")

    # Drop deferred FK before dropping users
    op.drop_constraint("fk_tenants_owner_user", "tenants", type_="foreignkey")
    op.drop_table("users")
    op.drop_table("tenants")

    # ── Drop enum types ──────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS dunning_status")
    op.execute("DROP TYPE IF EXISTS audit_action")
    op.execute("DROP TYPE IF EXISTS discount_applies_to")
    op.execute("DROP TYPE IF EXISTS discount_type")
    op.execute("DROP TYPE IF EXISTS payment_method")
    op.execute("DROP TYPE IF EXISTS invoice_status")
    op.execute("DROP TYPE IF EXISTS subscription_status")
    op.execute("DROP TYPE IF EXISTS billing_period")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS tenant_status")
