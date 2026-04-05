"""
Base repository with tenant-scoping for all database operations.

Architecture:
  BaseRepository — standard CRUD, always applies WHERE tenant_id = X.
  SuperAdminRepository — no tenant filter (cross-tenant access).
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import NotFoundException
from app.models.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Tenant-scoped repository.

    Every query is filtered by ``tenant_id`` AND ``deleted_at IS NULL``.
    """

    model: Type[T]

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    # ── query scoping ────────────────────────────────────────────
    def _scope(self, query: Select[tuple[T]]) -> Select[tuple[T]]:
        """Apply tenant isolation + soft-delete filter."""
        return query.where(
            and_(
                self.model.tenant_id == self.tenant_id,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),
            )
        )

    def _base_query(self) -> Select[tuple[T]]:
        """Scoped SELECT for this model."""
        return self._scope(select(self.model))

    # ── READ ─────────────────────────────────────────────────────
    async def find_all(
        self,
        *,
        filters: list[Any] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[T]:
        query = self._base_query()
        if filters:
            query = query.where(*filters)
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.unique().scalars().all()

    async def find_by_id(self, entity_id: uuid.UUID) -> T:
        query = self._base_query().where(self.model.id == entity_id)
        result = await self.db.execute(query)
        entity = result.unique().scalar_one_or_none()
        if entity is None:
            raise NotFoundException(
                f"{self.model.__tablename__} with id {entity_id} not found."
            )
        return entity

    async def find_one(self, *filters: Any) -> Optional[T]:
        query = self._base_query().where(*filters)
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def count(self, *filters: Any) -> int:
        from sqlalchemy import func as sa_func

        query = self._scope(
            select(sa_func.count()).select_from(self.model)
        )
        if filters:
            query = query.where(*filters)
        result = await self.db.execute(query)
        return result.scalar_one()

    # ── CREATE ───────────────────────────────────────────────────
    async def create(self, data: dict[str, Any]) -> T:
        """Insert a new row, auto-injecting ``tenant_id``."""
        data["tenant_id"] = self.tenant_id
        entity = self.model(**data)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    # ── UPDATE ───────────────────────────────────────────────────
    async def update(
        self, entity_id: uuid.UUID, data: dict[str, Any]
    ) -> T:
        entity = await self.find_by_id(entity_id)
        for key, value in data.items():
            if key in ("id", "tenant_id", "created_at"):
                continue  # immutable fields
            setattr(entity, key, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    # ── DELETE ───────────────────────────────────────────────────
    async def soft_delete(self, entity_id: uuid.UUID) -> None:
        entity = await self.find_by_id(entity_id)
        entity.soft_delete()
        await self.db.flush()


class SuperAdminRepository(BaseRepository[T]):
    """
    Cross-tenant repository for super_admin operations.

    Overrides ``_scope`` to remove tenant filtering entirely.
    **Never** inject this into company or portal_user services.
    """

    def __init__(self, db: AsyncSession) -> None:
        # tenant_id not used; call super with a dummy
        super().__init__(db, tenant_id=uuid.UUID(int=0))

    def _scope(self, query: Select[tuple[T]]) -> Select[tuple[T]]:
        """No tenant filter — super_admin sees everything."""
        return query.where(self.model.deleted_at.is_(None))
