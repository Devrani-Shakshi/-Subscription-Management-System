# Subscription Management System

Multi-tenant SaaS backend for subscription billing, invoicing, and customer management.

## Architecture

| Role | Scope |
|------|-------|
| **super_admin** | Platform-wide. No tenant. Sees all companies. |
| **company** | Full CRUD on own tenant's data only. |
| **portal_user** | Self-service. Sees own subscriptions/invoices. |

**Tenant isolation** enforced at 3 layers:
1. ORM — `BaseRepository` scopes every query by `tenant_id`
2. Middleware — `tenant_id` injected from JWT, never from request body
3. PostgreSQL RLS — `SET LOCAL app.tenant_id` per transaction

## Tech Stack

- **Python 3.11+** / FastAPI / Pydantic v2
- **SQLAlchemy 2.x** (async) + Alembic migrations
- **PostgreSQL** with Row-Level Security
- **Redis** for session family tracking

## Quick Start

```bash
# 1. Clone & install
git clone <repo-url> && cd -Subscription-Management-System
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 3. Run migrations
alembic upgrade head

# 4. Run tests (no PostgreSQL needed — uses SQLite)
python -m pytest tests/ -v
```

## Project Structure

```
app/
├── core/               # Config, enums, database engine
├── models/             # SQLAlchemy models (1 file per table)
├── repositories/       # BaseRepository + SuperAdminRepository
├── dependencies/       # FastAPI Depends() — DB session, auth
├── exceptions/         # AppException hierarchy + handlers
└── schemas/            # Pydantic request/response schemas

alembic/
└── versions/
    └── 001_initial_schema.py   # Full schema + RLS + indexes

tests/
├── conftest.py         # Fixtures (SQLite + PG type adapters)
├── test_models.py      # Model creation, soft-delete, to_dict
└── test_repositories.py # Tenant-scoped CRUD, isolation
```

## Schema (20 tables)

**Identity:** `tenants` · `users` · `sessions` · `failed_login_attempts`

**Catalog:** `products` · `product_variants` · `plans`

**Subscriptions:** `subscriptions` · `subscription_lines` · `quotation_templates`

**Billing:** `invoices` · `invoice_lines` · `payments` · `discounts` · `taxes`

**Operations:** `audit_log` · `churn_scores` · `dunning_schedules` · `revenue_recognition`

## License

MIT
