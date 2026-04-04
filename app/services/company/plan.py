"""
PlanService — CRUD + soft-delete guard for active subscriptions.

Business rules:
- Cannot delete a plan with active subscriptions.
- Plan preview returns customer-facing card data.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from app.core.enums import SubscriptionStatus
from app.exceptions.base import ConflictException
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.schemas.company import PlanPreviewResponse
from app.services.company.base_entity import BaseEntityService


class PlanService(BaseEntityService[Plan]):
    """Plan lifecycle management."""

    model = Plan

    async def _pre_delete(self, entity_id: uuid.UUID) -> None:
        """Block delete if plan has active subscriptions."""
        active_statuses = {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CONFIRMED,
        }
        query = (
            select(Subscription.id)
            .where(
                Subscription.plan_id == entity_id,
                Subscription.tenant_id == self.tenant_id,
                Subscription.status.in_(active_statuses),
                Subscription.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self.db.execute(query)
        if result.scalar_one_or_none() is not None:
            raise ConflictException(
                "Plan has active subscriptions."
            )

    async def get_preview(self, plan_id: uuid.UUID) -> PlanPreviewResponse:
        """Return plan card preview data as customer would see it."""
        plan = await self.get_by_id(plan_id)
        return PlanPreviewResponse(
            id=plan.id,
            name=plan.name,
            price=plan.price,
            billing_period=plan.billing_period,
            features=plan.features_json,
            flags=plan.flags_json,
        )
