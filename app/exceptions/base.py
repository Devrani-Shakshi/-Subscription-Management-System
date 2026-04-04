"""
Structured exception hierarchy.
Every exception carries a machine-readable `code` for frontend consumption.
"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base for all domain exceptions."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        code: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.extra = extra or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.extra:
            payload["errors"] = self.extra.get("errors", [])
        return payload


# ── Auth ─────────────────────────────────────────────────────────
class AuthException(AppException):
    status_code = 401
    code = "AUTH_ERROR"
    message = "Authentication failed."


class ForbiddenException(AppException):
    status_code = 403
    code = "FORBIDDEN"
    message = "Access denied."


# ── Data ─────────────────────────────────────────────────────────
class NotFoundException(AppException):
    status_code = 404
    code = "NOT_FOUND"
    message = "Requested resource not found."


class ConflictException(AppException):
    status_code = 409
    code = "CONFLICT"
    message = "Resource conflict."


# ── Validation ───────────────────────────────────────────────────
class ValidationException(AppException):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "One or more fields failed validation."

    def __init__(
        self,
        errors: list[dict[str, str]],
        message: str | None = None,
    ) -> None:
        super().__init__(
            message=message or self.message,
            extra={"errors": errors},
        )


# ── Rate Limiting ────────────────────────────────────────────────
class RateLimitException(AppException):
    status_code = 429
    code = "RATE_LIMIT"
    message = "Too many requests. Please try again later."


# ── Service ──────────────────────────────────────────────────────
class ServiceException(AppException):
    status_code = 500
    code = "SERVICE_ERROR"
    message = "Internal service error."
