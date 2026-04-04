"""
Revenue recognition service — orchestrates strategy execution and DB persistence.

Provides:
- process: run recognition for a single invoice (idempotent UPSERT)
- get_timeline: aggregate recognized/deferred revenue by month
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.revenue_recognition import RevenueRecognition
from app.services.base import BaseService
from app.services.revenue.strategies import (
    MilestoneRecognitionStrategy,
    RatableRecognitionStrategy,
    RecognitionStrategy,
    RevenueRecognitionRow,
)


class RevenueRecognitionService(BaseService):
    """Tenant-scoped revenue recognition operations."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        strategy: RecognitionStrategy | None = None,
    ) -> None:
        super().__init__(db)
        self.tenant_id = tenant_id
        self._strategy = strategy or RatableRecognitionStrategy()

    async def process(self, invoice_id: uuid.UUID) -> int:
        """
        Recognize revenue for an invoice (idempotent).

        Deletes existing rows for this invoice and re-creates.
        Returns the number of recognition rows created.
        """
        # Fetch invoice
        result = await self.db.execute(
            select(Invoice).where(
                and_(
                    Invoice.id == invoice_id,
                    Invoice.tenant_id == self.tenant_id,
                    Invoice.deleted_at.is_(None),
                )
            )
        )
        invoice = result.scalar_one_or_none()
        if invoice is None:
            return 0

        # Delete existing recognition rows (idempotent)
        await self.db.execute(
            delete(RevenueRecognition).where(
                and_(
                    RevenueRecognition.invoice_id == invoice_id,
                    RevenueRecognition.tenant_id == self.tenant_id,
                )
            )
        )

        # Generate recognition rows via strategy
        rows: list[RevenueRecognitionRow] = self._strategy.recognize(invoice)

        # Persist
        for row in rows:
            entry = RevenueRecognition(
                tenant_id=self.tenant_id,
                invoice_id=invoice_id,
                recognized_amount=row.recognized_amount,
                recognition_date=row.recognition_date,
                period=row.period,
            )
            self.db.add(entry)

        await self.db.flush()
        return len(rows)

    async def get_timeline(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get revenue recognition timeline aggregated by month.

        Returns list of { month, recognized, deferred, cumulative }.
        """
        base_filter = and_(
            RevenueRecognition.tenant_id == self.tenant_id,
            RevenueRecognition.deleted_at.is_(None),
        )

        # Total revenue to calculate deferred
        total_q = (
            select(
                func.coalesce(
                    func.sum(RevenueRecognition.recognized_amount), 0
                )
            )
            .select_from(RevenueRecognition)
            .where(base_filter)
        )
        total_result = await self.db.execute(total_q)
        total_recognized = Decimal(str(total_result.scalar_one()))

        # Aggregate by period
        query = (
            select(
                RevenueRecognition.period,
                func.sum(RevenueRecognition.recognized_amount).label("amount"),
            )
            .where(base_filter)
            .group_by(RevenueRecognition.period)
            .order_by(RevenueRecognition.period)
        )

        if start_date:
            query = query.where(
                RevenueRecognition.recognition_date >= start_date
            )
        if end_date:
            query = query.where(
                RevenueRecognition.recognition_date <= end_date
            )

        result = await self.db.execute(query)
        rows = result.all()

        timeline: list[dict[str, Any]] = []
        cumulative = Decimal("0")

        for row in rows:
            recognized = Decimal(str(row.amount))
            cumulative += recognized
            deferred = total_recognized - cumulative

            timeline.append(
                {
                    "month": row.period,
                    "recognized": str(recognized),
                    "deferred": str(max(deferred, Decimal("0"))),
                    "cumulative": str(cumulative),
                }
            )

        return timeline


class CrossTenantRevenueService(BaseService):
    """Super-admin cross-tenant revenue recognition view."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_timeline(self) -> list[dict[str, Any]]:
        """Aggregate across all tenants."""
        query = (
            select(
                RevenueRecognition.period,
                func.sum(RevenueRecognition.recognized_amount).label("amount"),
                func.count(
                    func.distinct(RevenueRecognition.tenant_id)
                ).label("tenant_count"),
            )
            .where(RevenueRecognition.deleted_at.is_(None))
            .group_by(RevenueRecognition.period)
            .order_by(RevenueRecognition.period)
        )

        result = await self.db.execute(query)
        rows = result.all()

        cumulative = Decimal("0")
        timeline: list[dict[str, Any]] = []

        for row in rows:
            recognized = Decimal(str(row.amount))
            cumulative += recognized
            timeline.append(
                {
                    "month": row.period,
                    "recognized": str(recognized),
                    "cumulative": str(cumulative),
                    "tenant_count": row.tenant_count,
                }
            )

        return timeline
