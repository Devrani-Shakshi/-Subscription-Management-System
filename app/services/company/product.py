"""
ProductService — CRUD + variants + soft-delete guard.

Business rules:
- Product name unique within tenant.
- Cannot delete a product used in active subscription lines.
- Variant management scoped to the parent product.
"""

from __future__ import annotations

import uuid
from typing import Any, Sequence

from pydantic import BaseModel as PydanticBase
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SubscriptionStatus
from app.exceptions.base import ConflictException, ValidationException
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.subscription_line import SubscriptionLine
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository
from app.services.company.base_entity import BaseEntityService


class ProductService(BaseEntityService[Product]):
    """Full product lifecycle including variants."""

    model = Product

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(db, tenant_id)
        self._variant_repo: BaseRepository[ProductVariant] = BaseRepository(
            self.db, self.tenant_id,
        )
        self._variant_repo.model = ProductVariant

    # ── Business-rule hooks ──────────────────────────────────────

    async def _pre_create(self, data: dict[str, Any]) -> None:
        """Enforce unique product name within tenant."""
        existing = await self.repo.find_one(Product.name == data["name"])
        if existing:
            raise ValidationException(
                [{"field": "name", "message": "Product name already exists."}]
            )

    async def _pre_update(
        self, entity_id: uuid.UUID, data: dict[str, Any],
    ) -> None:
        if "name" in data:
            existing = await self.repo.find_one(
                and_(
                    Product.name == data["name"],
                    Product.id != entity_id,
                ),
            )
            if existing:
                raise ValidationException(
                    [{"field": "name", "message": "Product name already exists."}]
                )

    async def _pre_delete(self, entity_id: uuid.UUID) -> None:
        """Block delete if product is in an active subscription line."""
        active_statuses = {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CONFIRMED,
        }
        query = (
            select(SubscriptionLine.id)
            .join(
                Subscription,
                SubscriptionLine.subscription_id == Subscription.id,
            )
            .where(
                SubscriptionLine.product_id == entity_id,
                SubscriptionLine.tenant_id == self.tenant_id,
                SubscriptionLine.deleted_at.is_(None),
                Subscription.status.in_(active_statuses),
                Subscription.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self.db.execute(query)
        if result.scalar_one_or_none() is not None:
            raise ConflictException(
                "Product is used in active subscriptions."
            )

    # ── Variant operations ───────────────────────────────────────

    async def list_variants(
        self, product_id: uuid.UUID,
    ) -> Sequence[ProductVariant]:
        """List all variants for a product (validates product exists)."""
        await self.get_by_id(product_id)  # 404 if missing
        return await self._variant_repo.find_all(
            filters=[ProductVariant.product_id == product_id],
        )

    async def create_variant(
        self,
        product_id: uuid.UUID,
        dto: PydanticBase,
    ) -> ProductVariant:
        """Add a variant to a product."""
        await self.get_by_id(product_id)
        data = dto.model_dump(exclude_unset=False)
        data["product_id"] = product_id
        return await self._variant_repo.create(data)

    async def delete_variant(
        self,
        product_id: uuid.UUID,
        variant_id: uuid.UUID,
    ) -> None:
        """Remove a variant. Validates it belongs to the product."""
        await self.get_by_id(product_id)
        variant = await self._variant_repo.find_by_id(variant_id)
        if variant.product_id != product_id:
            from app.exceptions.base import NotFoundException
            raise NotFoundException("Variant not found on this product.")
        await self._variant_repo.soft_delete(variant_id)
