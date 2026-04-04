"""
Failed login attempts — rate-limiting brute-force attacks.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class FailedLoginAttempt(BaseModel):
    __tablename__ = "failed_login_attempts"

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    ip: Mapped[str] = mapped_column(String(50), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return f"<FailedLogin {self.email!r} @ {self.attempted_at}>"
