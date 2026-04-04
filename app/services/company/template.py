"""
TemplateService — quotation template CRUD.

Validates that referenced plan_id exists within the tenant.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.exceptions.base import ValidationException
from app.models.plan import Plan
from app.models.quotation_template import QuotationTemplate
from app.repositories.base import BaseRepository
from app.services.company.base_entity import BaseEntityService


class TemplateService(BaseEntityService[QuotationTemplate]):
    """Quotation template management."""

    model = QuotationTemplate

    async def _validate_plan(self, plan_id: uuid.UUID) -> None:
        """Ensure referenced plan belongs to this tenant."""
        plan_repo: BaseRepository[Plan] = BaseRepository(
            self.db, self.tenant_id,
        )
        plan_repo.model = Plan
        plan = await plan_repo.find_one(Plan.id == plan_id)
        if plan is None:
            raise ValidationException(
                [{"field": "plan_id", "message": "Plan not found."}]
            )

    async def _pre_create(self, data: dict[str, Any]) -> None:
        await self._validate_plan(data["plan_id"])

    async def _pre_update(
        self, entity_id: uuid.UUID, data: dict[str, Any],
    ) -> None:
        if "plan_id" in data:
            await self._validate_plan(data["plan_id"])
