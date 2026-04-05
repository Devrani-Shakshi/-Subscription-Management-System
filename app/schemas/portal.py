"""
Portal Pydantic v2 schemas — portal_user self-service endpoints.

Rules:
- All strings stripped + HTML-sanitized.
- Strict password validation with pattern matching.
- No raw dicts — structured response models.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import PaymentMethod

_HTML_TAG = re.compile(r"<[^>]+>")
_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()\-_+=\[\]{}|;:'\",.<>?/`~\\])"
    r".{8,}$"
)


def _strip_html(v: str) -> str:
    return _HTML_TAG.sub("", v)


def _sanitize(v: str) -> str:
    return _strip_html(v.strip())


# ═══════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════


class PortalProfileResponse(BaseModel):
    """Read-only portal user profile matching frontend expectations."""

    name: str
    email: str
    street: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    zip: str = ""
    created_at: Optional[datetime] = None


class PortalProfileUpdateRequest(BaseModel):
    """Update editable profile fields (name only)."""

    name: str = Field(..., min_length=2, max_length=255)

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return _sanitize(v)


class PortalAddressUpdateRequest(BaseModel):
    """Update billing address."""

    street: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., min_length=1, max_length=255)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)

    @field_validator("street", "city", "state", "postal_code", "country", mode="before")
    @classmethod
    def sanitize_all(cls, v: str) -> str:
        return _sanitize(v)

    def to_address_string(self) -> str:
        """Combine fields into a single address string."""
        return f"{self.street}, {self.city}, {self.state} {self.postal_code}, {self.country}"


# ═══════════════════════════════════════════════════════════════
# Password Change
# ═══════════════════════════════════════════════════════════════


class PasswordChangeRequest(BaseModel):
    """Change password — requires current password verification."""

    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("current_password", mode="before")
    @classmethod
    def strip_current(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("Current password is required.")
        return v.strip()

    @field_validator("new_password", mode="before")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        v = v.strip()
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters with "
                "1 uppercase, 1 lowercase, and 1 special character."
            )
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordChangeRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self

    @model_validator(mode="after")
    def not_same_as_current(self) -> "PasswordChangeRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current.")
        return self


# ═══════════════════════════════════════════════════════════════
# Sessions
# ═══════════════════════════════════════════════════════════════


class SessionResponse(BaseModel):
    """Active session info matching frontend expectations."""

    id: UUID
    device: str
    ip: str
    lastActive: datetime
    isCurrent: bool = False


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int


# ═══════════════════════════════════════════════════════════════
# Payment History
# ═══════════════════════════════════════════════════════════════


class PortalPaymentResponse(BaseModel):
    """Portal-facing payment history entry matching frontend expectation."""

    id: UUID
    date: datetime
    invoiceNumber: str = ""
    amount: Decimal
    method: str
    status: str = "success"


class PortalPaymentListResponse(BaseModel):
    items: list[PortalPaymentResponse]
    total: int
    has_overdue: bool = False
