"""
Tests for BaseRepository — tenant-scoped CRUD operations.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Type

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.tenant import Tenant
from app.exceptions.base import NotFoundException
from app.repositories.base import BaseRepository, SuperAdminRepository


class ProductRepository(BaseRepository[Product]):
    model = Product


class SuperAdminProductRepository(SuperAdminRepository[Product]):
    model = Product


@pytest.mark.asyncio
class TestBaseRepository:
    async def test_create_auto_injects_tenant(
        self, db: AsyncSession, tenant: Tenant
    ):
        repo = ProductRepository(db, tenant.id)
        product = await repo.create({
            "name": "Test Product",
            "type": "digital",
            "sales_price": Decimal("19.99"),
            "cost_price": Decimal("5.00"),
        })
        assert product.tenant_id == tenant.id
        assert product.name == "Test Product"

    async def test_find_by_id(
        self, db: AsyncSession, tenant: Tenant, product: Product
    ):
        repo = ProductRepository(db, tenant.id)
        found = await repo.find_by_id(product.id)
        assert found.id == product.id

    async def test_find_by_id_not_found(
        self, db: AsyncSession, tenant: Tenant
    ):
        repo = ProductRepository(db, tenant.id)
        with pytest.raises(NotFoundException):
            await repo.find_by_id(uuid.uuid4())

    async def test_find_all(
        self, db: AsyncSession, tenant: Tenant, product: Product
    ):
        repo = ProductRepository(db, tenant.id)
        products = await repo.find_all()
        assert len(products) >= 1
        assert any(p.id == product.id for p in products)

    async def test_update(
        self, db: AsyncSession, tenant: Tenant, product: Product
    ):
        repo = ProductRepository(db, tenant.id)
        updated = await repo.update(product.id, {"name": "Renamed"})
        assert updated.name == "Renamed"

    async def test_soft_delete(
        self, db: AsyncSession, tenant: Tenant, product: Product
    ):
        repo = ProductRepository(db, tenant.id)
        await repo.soft_delete(product.id)
        # After soft delete, find_by_id should not find it
        with pytest.raises(NotFoundException):
            await repo.find_by_id(product.id)

    async def test_tenant_isolation(self, db: AsyncSession, tenant: Tenant):
        """Products from one tenant must not be visible with another tenant_id."""
        repo_a = ProductRepository(db, tenant.id)
        product = await repo_a.create({
            "name": "Isolated",
            "type": "digital",
            "sales_price": Decimal("10.00"),
            "cost_price": Decimal("2.00"),
        })

        other_tenant_id = uuid.uuid4()
        repo_b = ProductRepository(db, other_tenant_id)
        results = await repo_b.find_all()
        assert not any(p.id == product.id for p in results)


@pytest.mark.asyncio
class TestSuperAdminRepository:
    async def test_sees_all_tenants(
        self, db: AsyncSession, tenant: Tenant, product: Product
    ):
        repo = SuperAdminProductRepository(db)
        products = await repo.find_all()
        assert len(products) >= 1
