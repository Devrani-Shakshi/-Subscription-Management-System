"""
Portal Service — business logic for portal_user self-service.

Responsibilities:
- Profile read / update
- Password change (with current-password verification)
- Billing address update
- Session listing / revocation / revoke-all
- Payment history with overdue invoice detection
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus, UserRole
from app.core.security import hash_password, hash_token, verify_password
from app.exceptions.base import (
    AuthException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.session import Session
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.portal import (
    PasswordChangeRequest,
    PortalAddressUpdateRequest,
    PortalPaymentListResponse,
    PortalPaymentResponse,
    PortalProfileResponse,
    PortalProfileUpdateRequest,
    SessionListResponse,
    SessionResponse,
)
from app.services.base import BaseService
from app.services.token_family import TokenFamilyService


class PortalService(BaseService):
    """All portal_user self-service business logic."""

    def __init__(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> None:
        super().__init__(db)
        self._user_id = user_id
        self._tenant_id = tenant_id

    # ── PROFILE ─────────────────────────────────────────────────

    async def get_profile(self) -> PortalProfileResponse:
        """Return full profile for the authenticated portal_user."""
        user = await self._require_user()
        tenant_name = await self._get_tenant_name()

        return PortalProfileResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            tenant_id=user.tenant_id,
            tenant_name=tenant_name,
            billing_address=getattr(user, "billing_address", None),
            created_at=user.created_at,
        )

    async def update_profile(
        self, dto: PortalProfileUpdateRequest,
    ) -> PortalProfileResponse:
        """Update portal_user name."""
        user = await self._require_user()
        user.name = dto.name
        await self.db.flush()
        await self.db.refresh(user)
        return await self.get_profile()

    async def update_address(
        self, dto: PortalAddressUpdateRequest,
    ) -> PortalProfileResponse:
        """Update billing address (stored as string on user)."""
        user = await self._require_user()
        # Store combined address string
        if hasattr(user, "billing_address"):
            user.billing_address = dto.to_address_string()
        await self.db.flush()
        await self.db.refresh(user)
        return await self.get_profile()

    # ── PASSWORD CHANGE ─────────────────────────────────────────

    async def change_password(
        self, dto: PasswordChangeRequest,
    ) -> dict:
        """Change password — verifies current password first."""
        user = await self._require_user()

        if not user.password_hash:
            raise ValidationException(
                [{"field": "current_password", "message": "No password set."}]
            )

        if not verify_password(dto.current_password, user.password_hash):
            raise ValidationException(
                [{"field": "current_password", "message": "Current password is incorrect."}]
            )

        user.password_hash = hash_password(dto.new_password)
        await self.db.flush()

        return {"message": "Password changed successfully."}

    # ── SESSIONS ────────────────────────────────────────────────

    async def list_sessions(
        self,
        current_session_family_id: uuid.UUID | None = None,
    ) -> SessionListResponse:
        """List all active sessions for this user."""
        result = await self.db.execute(
            select(Session)
            .where(
                Session.user_id == self._user_id,
                Session.revoked_at.is_(None),
                Session.expires_at > datetime.now(timezone.utc),
            )
            .order_by(Session.created_at.desc())
        )
        sessions = result.scalars().all()

        items = [
            SessionResponse(
                id=s.id,
                device=s.device_fingerprint,
                ip_subnet=s.ip_subnet,
                last_active=s.created_at,
                is_current=(
                    current_session_family_id is not None
                    and s.family_id == current_session_family_id
                ),
            )
            for s in sessions
        ]

        return SessionListResponse(items=items, total=len(items))

    async def revoke_session(self, session_id: uuid.UUID) -> dict:
        """Revoke a specific session by ID."""
        result = await self.db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.user_id == self._user_id,
                Session.revoked_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise NotFoundException("Session not found.")

        session.revoked_at = datetime.now(timezone.utc)
        # Also revoke in Redis
        await TokenFamilyService.revoke_family(session.family_id)
        await self.db.flush()

        return {"message": "Session revoked."}

    async def revoke_all_sessions(
        self,
        exclude_family_id: uuid.UUID | None = None,
    ) -> dict:
        """Revoke ALL sessions for this user, optionally keeping one."""
        query = select(Session).where(
            Session.user_id == self._user_id,
            Session.revoked_at.is_(None),
        )
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        now = datetime.now(timezone.utc)
        revoked_count = 0
        for s in sessions:
            if exclude_family_id and s.family_id == exclude_family_id:
                continue
            s.revoked_at = now
            await TokenFamilyService.revoke_family(s.family_id)
            revoked_count += 1

        await self.db.flush()

        return {
            "message": f"{revoked_count} session(s) revoked.",
            "revoked_count": revoked_count,
        }

    # ── PAYMENT HISTORY ─────────────────────────────────────────

    async def list_payments(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> PortalPaymentListResponse:
        """List payment history for the portal user."""
        # Payments with invoice join for invoice_number
        query = (
            select(Payment)
            .where(
                Payment.customer_id == self._user_id,
                Payment.tenant_id == self._tenant_id,
                Payment.deleted_at.is_(None),
            )
            .order_by(Payment.paid_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        payments = result.scalars().all()

        # Count total
        count_result = await self.db.execute(
            select(func.count(Payment.id)).where(
                Payment.customer_id == self._user_id,
                Payment.tenant_id == self._tenant_id,
                Payment.deleted_at.is_(None),
            )
        )
        total = count_result.scalar() or 0

        # Check overdue invoices
        overdue_result = await self.db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.customer_id == self._user_id,
                Invoice.tenant_id == self._tenant_id,
                Invoice.status == InvoiceStatus.OVERDUE,
                Invoice.deleted_at.is_(None),
            )
        )
        has_overdue = (overdue_result.scalar() or 0) > 0

        items = []
        for p in payments:
            inv_number = None
            if p.invoice:
                inv_number = p.invoice.invoice_number
            items.append(
                PortalPaymentResponse(
                    id=p.id,
                    amount=p.amount,
                    method=p.method,
                    invoice_id=p.invoice_id,
                    invoice_number=inv_number,
                    paid_at=p.paid_at,
                    created_at=p.created_at,
                )
            )

        return PortalPaymentListResponse(
            items=items,
            total=total,
            has_overdue=has_overdue,
        )

    # ═══════════════════════════════════════════════════════════════
    # Private helpers
    # ═══════════════════════════════════════════════════════════════

    async def _require_user(self) -> User:
        """Load and return the current portal user."""
        result = await self.db.execute(
            select(User).where(
                User.id == self._user_id,
                User.deleted_at.is_(None),
            )
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundException("User not found.")
        return user

    async def _get_tenant_name(self) -> str | None:
        """Get tenant name for branding."""
        result = await self.db.execute(
            select(Tenant.name).where(Tenant.id == self._tenant_id)
        )
        return result.scalar_one_or_none()
