"""
Product model — tenant-scoped catalog items.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.product_variant import ProductVariant


class Product(BaseModel):
    __tablename__ = "products"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    sales_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    # ── relationships ────────────────────────────────────────────
    variants: Mapped[list["ProductVariant"]] = relationship(
        "ProductVariant", back_populates="product", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Product {self.name!r}>"
