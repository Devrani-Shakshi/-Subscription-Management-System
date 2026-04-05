"""
Quotation template model — reusable proposal templates.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.plan import Plan

class QuotationTemplate(BaseModel):
    __tablename__ = "quotation_templates"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    validity_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False,
    )

    plan: Mapped["Plan"] = relationship("Plan", lazy="joined")

    def __repr__(self) -> str:
        return f"<QuotationTemplate {self.name!r}>"
