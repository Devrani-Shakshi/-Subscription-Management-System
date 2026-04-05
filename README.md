#video link:https://drive.google.com/file/d/1AItn4MRDJ0xaR-WkQQBrxTel_xpXTRPb/view?usp=sharing

# Subscription Management System

A comprehensive, production-ready Multi-tenant SaaS platform for seamless subscription billing, invoicing, modern data analytics, and customer management. Featuring a complete full-stack implementation composed of a robust FastAPI backend and a dynamic React+Vite UI system.

## Key Features

* **Multi-tenant Architecture:** Total isolation spanning from PostgreSQL Row-Level Security down to frontend routing and UI visualization.
* **Modern Analytics Dashboard:** Native React+Recharts visualization displaying deep MRR computations, Churn Risk scores natively hooked, Active Subscriptions tracking, and Dunning Management alerts.
* **Full E2E Billing and Products:** Dynamic pricing plans, product variants, automatic payment terms generation, quotation templates, automated discounts, and taxes routing.
* **Automated Seed Environment:** Advanced unified SQL procedures to automatically simulate massive inter-related datasets for demonstrations and unit tests.
* **State of the Art Tech Stack:** Written symmetrically in robust typing layers via Python 3.11 Pydantic and TypeScript Zod to enforce integrity end to end.

## Architecture

| Role | Scope |
|------|-------|
| **super_admin** | Platform-wide. No tenant. Sees all companies. |
| **company** | Full CRUD on own tenant's data only. Access to Dashboard & Bulk tools. |
| **portal_user** | Self-service. Sees own subscriptions/invoices only. |

**Tenant isolation** enforced at 3 key layers:
1. ORM — `BaseRepository` scopes every query tightly by `tenant_id`
2. API Layer — `tenant_id` intelligently injected from JWT.
3. PostgreSQL RLS — `SET LOCAL app.tenant_id` strictly per transaction.

## Tech Stack

**Backend:**
- **Python 3.11+** / FastAPI / Pydantic v2
- **SQLAlchemy 2.x** (async) + Alembic migrations
- **PostgreSQL 15+** with Enums, Row-Level Security constraints.
- **Redis** caching mechanisms for concurrent dashboard queries.

**Frontend:**
- **React 18** / Vite / TypeScript
- **Tailwind CSS** / Lucide Icons
- **Recharts** data intelligence graphics
- **TanStack Query** standard caching capabilities.

## Quick Start (Backend)

```bash
# 1. Clone & install dependencies
git clone <repo-url> && cd -Subscription-Management-System
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your PostgreSQL credentials (e.g. postgres://postgres:postgres@localhost:5432)

# 3. Apply Schema Migrations
alembic upgrade head

# 4. Generate Demo/Test Data (Optional but recommended)
psql -U postgres -d submanager -f inject_nova.sql

# 5. Bring server online
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
## Quick Start (Frontend)

```bash
cd frontend
npm install
npm run dev

# Browse at http://localhost:3000
# Demo login (if you ran inject_nova.sql!): demo@demodata.com / Password123!
```

## Production Schema (20 modules)

- **Identity System:** `tenants` · `users` · `sessions` · `failed_login_attempts`
- **Catalog Management:** `products` · `product_variants` · `plans`
- **Subscription Engines:** `subscriptions` · `subscription_lines` · `quotation_templates`
- **Inbound Billing:** `invoices` · `invoice_lines` · `payments` · `discounts` · `taxes`
- **Intelligent Operations:** `audit_log` · `churn_scores` · `dunning_schedules` · `revenue_recognition`

## Testing

A robust SQLite-backed test harness evaluates core endpoints, security implementations, model properties, and RBAC policies entirely independent of Postgres environments.

```bash
python -m pytest tests/ -v
```

## License

MIT
