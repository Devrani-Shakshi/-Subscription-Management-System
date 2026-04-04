"""
Auth Pydantic v2 schemas — strict validation on every auth endpoint.

Rules:
- All strings stripped of whitespace.
- Emails lower-cased.
- Passwords: min 8 chars, 1 upper, 1 lower, 1 special.
"""

from __future__ import annotations

import re
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ── Helpers ──────────────────────────────────────────────────────
_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/`~\\])"
    r".{8,}$"
)

_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(v: str) -> str:
    return _HTML_TAG.sub("", v)


# ── Token payload (JWT claims, locked) ──────────────────────────
class TokenPayload(BaseModel):
    user_id: UUID
    role: Literal["super_admin", "company", "portal_user"]
    tenant_id: Optional[UUID] = None
    email: str


# ── Login ────────────────────────────────────────────────────────
class LoginSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return _strip_html(v.strip().lower())

    @field_validator("password", mode="before")
    @classmethod
    def strip_password(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("Password is required.")
        return v.strip()


class LoginResponse(BaseModel):
    access_token: str
    role: str
    tenant_id: Optional[UUID] = None


# ── Register (portal self-register) ─────────────────────────────
class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    name: str
    tenant_slug: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return _strip_html(v.strip().lower())

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = _strip_html(v.strip())
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return v

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        v = v.strip()
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters with "
                "1 uppercase, 1 lowercase, and 1 special character."
            )
        return v


# ── Invite accept ────────────────────────────────────────────────
class InviteAcceptSchema(BaseModel):
    token: str
    password: str
    name: str

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = _strip_html(v.strip())
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return v

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        v = v.strip()
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters with "
                "1 uppercase, 1 lowercase, and 1 special character."
            )
        return v


# ── Password reset ───────────────────────────────────────────────
class ResetRequestSchema(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return _strip_html(v.strip().lower())


class ResetPasswordSchema(BaseModel):
    token: UUID
    password: str
    confirm_password: str

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        v = v.strip()
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters with "
                "1 uppercase, 1 lowercase, and 1 special character."
            )
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordSchema":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


# ── Seed (super_admin bootstrap) ─────────────────────────────────
class SeedSchema(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return _strip_html(v.strip().lower())

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        v = v.strip()
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters with "
                "1 uppercase, 1 lowercase, and 1 special character."
            )
        return v


# ── Company creation by super_admin ──────────────────────────────
class CreateCompanySchema(BaseModel):
    name: str
    slug: str
    email: EmailStr

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = _strip_html(v.strip())
        if len(v) < 2:
            raise ValueError("Company name must be at least 2 characters.")
        return v

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = _strip_html(v.strip().lower())
        if not re.match(r"^[a-z0-9\-]{2,63}$", v):
            raise ValueError(
                "Slug must be 2-63 chars, lowercase alphanumeric and hyphens only."
            )
        return v

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return _strip_html(v.strip().lower())


# ── Portal customer invite ───────────────────────────────────────
class InviteCustomerSchema(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return _strip_html(v.strip().lower())


# ── Tenant public info ───────────────────────────────────────────
class TenantPublicSchema(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
