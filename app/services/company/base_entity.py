"""
BaseEntityService — generic CRUD service for tenant-scoped entities.

Every company service inherits this. Business logic goes in concrete
subclasses; this base handles the repetitive CRUD plumbing.

Architecture:
    BaseEntityService[T]
        ├── ProductService
        ├── PlanService
        ├── CustomerService
        ├── TemplateService
        ├── DiscountService
        └── TaxService
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, Sequence, Type, TypeVar

from pydantic import BaseModel as PydanticBase
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel
from app.repositories.base import BaseRepository

T = TypeVar("T", bound=BaseModel)


class BaseEntityService(Generic[T]):
    """
    Tenant-scoped CRUD service.

    Subclass contract:
        - Set ``model`` class attribute to the SQLAlchemy model.
        - Override hooks like ``_pre_create``, ``_pre_delete`` for
          business rules.
    """

    model: Type[T]

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.repo = self._make_repo()

    def _make_repo(self) -> BaseRepository[T]:
        """Create a tenant-scoped repository for our model."""
        repo: BaseRepository[T] = BaseRepository(self.db, self.tenant_id)
        repo.model = self.model
        return repo

    # ── CRUD ─────────────────────────────────────────────────────

    async def list_all(
        self,
        *,
        filters: list[Any] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[T]:
        return await self.repo.find_all(
            filters=filters, offset=offset, limit=limit,
        )

    async def get_by_id(self, entity_id: uuid.UUID) -> T:
        return await self.repo.find_by_id(entity_id)

    async def create(self, dto: PydanticBase) -> T:
        data = dto.model_dump(exclude_unset=False)
        await self._pre_create(data)
        entity = await self.repo.create(data)
        await self._post_create(entity)
        return entity

    async def update(
        self, entity_id: uuid.UUID, dto: PydanticBase,
    ) -> T:
        data = dto.model_dump(exclude_unset=True)
        await self._pre_update(entity_id, data)
        entity = await self.repo.update(entity_id, data)
        await self._post_update(entity)
        return entity

    async def delete(self, entity_id: uuid.UUID) -> None:
        await self._pre_delete(entity_id)
        await self.repo.soft_delete(entity_id)

    async def count(self, *filters: Any) -> int:
        return await self.repo.count(*filters)

    # ── Hooks (override in subclasses) ───────────────────────────

    async def _pre_create(self, data: dict[str, Any]) -> None:
        """Validate business rules before insert."""

    async def _post_create(self, entity: T) -> None:
        """Side-effects after insert."""

    async def _pre_update(
        self, entity_id: uuid.UUID, data: dict[str, Any],
    ) -> None:
        """Validate before update."""

    async def _post_update(self, entity: T) -> None:
        """Side-effects after update."""

    async def _pre_delete(self, entity_id: uuid.UUID) -> None:
        """Guard against invalid deletes (e.g. active subscriptions)."""
