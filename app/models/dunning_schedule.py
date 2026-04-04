"""
Dunning schedule — automated payment collection retry logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import DunningStatus
from app.models.base import BaseModel


class DunningSchedule(BaseModel):
    __tablename__ = "dunning_schedules"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[DunningStatus] = mapped_column(
        SAEnum(
            DunningStatus, name="dunning_status", create_constraint=True
        ),
        default=DunningStatus.PENDING,
        nullable=False,
    )
    result_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    def __repr__(self) -> str:
        return (
            f"<DunningSchedule invoice={self.invoice_id} "
            f"attempt={self.attempt_number}>"
        )
