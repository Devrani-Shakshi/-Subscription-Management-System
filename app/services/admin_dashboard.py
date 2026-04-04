"""
Super-admin dashboard service — platform-wide metrics and alerts.

Aggregates data across all tenants for the admin dashboard view.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SubscriptionStatus, TenantStatus, UserRole
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.admin import (
    SubscriptionRepository,
    TenantRepository,
    UserRepository,
)
from app.schemas.admin import (
    AlertItem,
    CompanyBreakdownRow,
    MetricCard,
    PlatformDashboardResponse,
    RevenueChartResponse,
    RevenueDataPoint,
)
from app.services.base import BaseService


class SuperAdminDashboardService(BaseService):
    """Platform-wide metrics, breakdown, and alerts."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._tenants = TenantRepository(db)
        self._users = UserRepository(db)
        self._subs = SubscriptionRepository(db)

    # ── MAIN DASHBOARD ───────────────────────────────────────────
    async def get_platform_metrics(self) -> PlatformDashboardResponse:
        """
        Build the full dashboard payload:
        - Metric cards (totals + deltas)
        - Company breakdown table
        - Platform alerts
        """
        metrics = await self._build_metric_cards()
        breakdown = await self._build_company_breakdown()
        alerts = await self._build_alerts()

        return PlatformDashboardResponse(
            metrics=metrics,
            company_breakdown=breakdown,
            alerts=alerts,
        )

    # ── REVENUE CHART DATA ───────────────────────────────────────
    async def get_revenue_chart(
        self, months: int = 12
    ) -> RevenueChartResponse:
        """
        Cross-tenant monthly revenue for the last N months.

        Uses payment records aggregated by month.
        """
        now = datetime.utcnow()
        start = now - timedelta(days=months * 30)

        query = (
            select(
                func.to_char(Payment.paid_at, 'YYYY-MM').label("month"),
                func.coalesce(func.sum(Payment.amount), 0).label("rev"),
                func.count(func.distinct(Payment.tenant_id)).label("cnt"),
            )
            .where(
                and_(
                    Payment.paid_at >= start,
                    Payment.deleted_at.is_(None),
                )
            )
            .group_by(func.to_char(Payment.paid_at, 'YYYY-MM'))
            .order_by(func.to_char(Payment.paid_at, 'YYYY-MM'))
        )

        result = await self.db.execute(query)
        rows = result.all()

        data_points = [
            RevenueDataPoint(
                month=row.month or "unknown",
                revenue=Decimal(str(row.rev)),
                tenant_count=int(row.cnt),
            )
            for row in rows
        ]
        total = sum(dp.revenue for dp in data_points)

        return RevenueChartResponse(
            data_points=data_points,
            total_revenue=total,
            period=f"Last {months} months",
        )

    # ═════════════════════════════════════════════════════════════
    # Private helpers
    # ═════════════════════════════════════════════════════════════

    async def _build_metric_cards(self) -> list[MetricCard]:
        """Build KPI metric cards."""
        # Total companies
        all_tenants, total_companies = await self._tenants.list_with_stats(
            offset=0, limit=1
        )
        # Active subscriptions
        total_active_subs = await self._subs.count_active_total()

        # New companies this month
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_q = (
            select(func.count())
            .select_from(Tenant)
            .where(
                and_(
                    Tenant.created_at >= month_start,
                    Tenant.deleted_at.is_(None),
                )
            )
        )
        new_result = await self.db.execute(new_q)
        new_companies = new_result.scalar_one()

        # Platform MRR (simplified: sum all payments)
        mrr_q = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .select_from(Payment)
            .where(Payment.deleted_at.is_(None))
        )
        mrr_result = await self.db.execute(mrr_q)
        platform_mrr = mrr_result.scalar_one()

        return [
            MetricCard(
                label="Total Companies",
                value=str(total_companies),
                trend="up" if new_companies > 0 else "flat",
            ),
            MetricCard(
                label="Active Subscriptions",
                value=str(total_active_subs),
            ),
            MetricCard(
                label="Platform MRR",
                value=f"${platform_mrr:,.2f}",
            ),
            MetricCard(
                label="New Companies (This Month)",
                value=str(new_companies),
                trend="up" if new_companies > 0 else "flat",
            ),
        ]

    async def _build_company_breakdown(self) -> list[CompanyBreakdownRow]:
        """Build the company breakdown table."""
        tenants, _ = await self._tenants.list_with_stats(
            offset=0, limit=100
        )
        rows: list[CompanyBreakdownRow] = []

        for t in tenants:
            active_subs = await self._subs.count_active_by_tenant(t.id)
            customers = await self._users.count_by_tenant(
                t.id, role="portal_user"
            )
            rows.append(
                CompanyBreakdownRow(
                    tenant_id=t.id,
                    name=t.name,
                    status=t.status,
                    mrr=Decimal("0.00"),
                    active_subs=active_subs,
                    customers=customers,
                )
            )

        return rows

    async def _build_alerts(self) -> list[AlertItem]:
        """Build platform alerts (trials expiring, suspended companies)."""
        alerts: list[AlertItem] = []
        now = datetime.utcnow()
        week_ahead = now + timedelta(days=7)

        # Trials expiring within 7 days
        trial_q = (
            select(Tenant)
            .where(
                and_(
                    Tenant.status == TenantStatus.TRIAL,
                    Tenant.trial_ends_at.isnot(None),
                    Tenant.trial_ends_at <= week_ahead,
                    Tenant.deleted_at.is_(None),
                )
            )
        )
        trial_result = await self.db.execute(trial_q)
        expiring = trial_result.scalars().all()

        for t in expiring:
            alerts.append(
                AlertItem(
                    severity="warning",
                    message=f"Trial for '{t.name}' expires soon.",
                    tenant_id=t.id,
                    tenant_name=t.name,
                )
            )

        # Suspended companies
        suspended_q = (
            select(Tenant)
            .where(
                and_(
                    Tenant.status == TenantStatus.SUSPENDED,
                    Tenant.deleted_at.is_(None),
                )
            )
        )
        suspended_result = await self.db.execute(suspended_q)
        suspended = suspended_result.scalars().all()

        for t in suspended:
            alerts.append(
                AlertItem(
                    severity="error",
                    message=f"'{t.name}' is suspended.",
                    tenant_id=t.id,
                    tenant_name=t.name,
                )
            )

        return alerts
