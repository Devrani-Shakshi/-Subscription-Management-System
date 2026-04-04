"""
Subscription line items — products within a subscription.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ARRAY, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.subscription import Subscription


class SubscriptionLine(BaseModel):
    __tablename__ = "subscription_lines"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    tax_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)), nullable=True
    )

    # ── relationships ────────────────────────────────────────────
    subscription: Mapped["Subscription"] = relationship(
        "Subscription", back_populates="lines", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<SubscriptionLine product={self.product_id} qty={self.qty}>"
