"""
Churn service — tenant-scoped churn score queries + batch computation.

Provides:
- list_churn_scores: paginated, sorted by score DESC
- compute_all_scores: batch compute for all portal_users in a tenant
- compute_for_customer: single customer score computation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ChurnRiskLevel, UserRole
from app.models.churn_score import ChurnScore
from app.models.user import User
from app.services.base import BaseService
from app.services.churn.engine import ChurnScoreEngine
from app.services.churn.signals import (
    DunningSignal,
    DowngradeSignal,
    LoginInactivitySignal,
    OverdueInvoiceSignal,
    PausedSignal,
)


def _default_engine() -> ChurnScoreEngine:
    """Create engine with all registered signals."""
    return ChurnScoreEngine(
        signals=[
            LoginInactivitySignal(),
            OverdueInvoiceSignal(),
            DowngradeSignal(),
            PausedSignal(),
            DunningSignal(),
        ]
    )


def risk_level(score: int) -> ChurnRiskLevel:
    """Classify score into risk level."""
    if score >= 70:
        return ChurnRiskLevel.HIGH
    if score >= 30:
        return ChurnRiskLevel.MEDIUM
    return ChurnRiskLevel.LOW


class ChurnService(BaseService):
    """Tenant-scoped churn score operations."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        engine: ChurnScoreEngine | None = None,
    ) -> None:
        super().__init__(db)
        self.tenant_id = tenant_id
        self._engine = engine or _default_engine()

    async def list_churn_scores(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        min_score: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List churn scores sorted by score DESC.

        Returns (items, total_count).
        """
        base_filter = and_(
            ChurnScore.tenant_id == self.tenant_id,
            ChurnScore.deleted_at.is_(None),
        )

        # Count
        count_q = (
            select(func.count())
            .select_from(ChurnScore)
            .where(base_filter)
        )
        if min_score is not None:
            count_q = count_q.where(ChurnScore.score >= min_score)
        total = (await self.db.execute(count_q)).scalar_one()

        # Items
        query = (
            select(ChurnScore)
            .where(base_filter)
            .order_by(ChurnScore.score.desc())
            .offset(offset)
            .limit(limit)
        )
        if min_score is not None:
            query = query.where(ChurnScore.score >= min_score)

        result = await self.db.execute(query)
        scores = result.scalars().all()

        # Enrich with customer info
        items: list[dict[str, Any]] = []
        for cs in scores:
            customer = await self._get_customer(cs.customer_id)
            items.append(
                {
                    "id": cs.id,
                    "customer_id": cs.customer_id,
                    "customer_name": customer.name if customer else "Unknown",
                    "customer_email": customer.email if customer else "",
                    "score": cs.score,
                    "risk_level": risk_level(cs.score).value,
                    "signals": cs.signals_json,
                    "computed_at": cs.computed_at,
                }
            )

        return items, total

    async def compute_all_scores(self) -> int:
        """
        Batch compute churn scores for all portal_users in this tenant.

        UPSERTS into churn_scores table. Returns count processed.
        """
        customers = await self._get_portal_users()
        count = 0

        for customer in customers:
            await self.compute_for_customer(customer)
            count += 1

        return count

    async def compute_for_customer(self, customer: User) -> ChurnScore:
        """Compute and UPSERT churn score for a single customer."""
        score, breakdown = await self._engine.score(customer, self.db)
        now = datetime.now(timezone.utc)

        # Check existing
        existing = await self._find_existing_score(customer.id)

        if existing:
            existing.score = score
            existing.signals_json = breakdown
            existing.computed_at = now
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        entry = ChurnScore(
            tenant_id=self.tenant_id,
            customer_id=customer.id,
            score=score,
            signals_json=breakdown,
            computed_at=now,
        )
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    # ── Private helpers ──────────────────────────────────────────

    async def _get_portal_users(self) -> Sequence[User]:
        """Get all active portal_users for this tenant."""
        query = select(User).where(
            and_(
                User.tenant_id == self.tenant_id,
                User.role == UserRole.PORTAL_USER,
                User.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _get_customer(
        self, customer_id: uuid.UUID
    ) -> User | None:
        """Lookup customer by ID."""
        result = await self.db.execute(
            select(User).where(User.id == customer_id)
        )
        return result.scalar_one_or_none()

    async def _find_existing_score(
        self, customer_id: uuid.UUID
    ) -> ChurnScore | None:
        """Find existing churn score for customer."""
        query = select(ChurnScore).where(
            and_(
                ChurnScore.tenant_id == self.tenant_id,
                ChurnScore.customer_id == customer_id,
                ChurnScore.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
