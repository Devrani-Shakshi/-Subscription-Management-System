"""
Invoice Service — business logic for invoice lifecycle.

Responsibilities:
- Generate invoices from subscriptions (via InvoiceBuilder)
- List / retrieve invoices (company + portal)
- Confirm / cancel / send invoices
- PDF generation dispatch
"""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InvoiceStatus
from app.exceptions.base import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.invoice import Invoice
from app.repositories.billing import (
    InvoiceRepository,
    SubscriptionRepository,
)
from app.services.base import BaseService
from app.services.billing.invoice_builder import InvoiceBuilder


class InvoiceService(BaseService):
    """All invoice business rules. Routers only call this."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> None:
        super().__init__(db)
        self._tenant_id = tenant_id
        self._repo = InvoiceRepository(db, tenant_id)
        self._sub_repo = SubscriptionRepository(db, tenant_id)

    # ── Generate ─────────────────────────────────────────────────

    async def generate_from_subscription(
        self,
        subscription_id: uuid.UUID,
    ) -> Invoice:
        """Create a draft invoice from a subscription's line items."""
        sub = await self._sub_repo.find_by_id(subscription_id)

        builder = InvoiceBuilder(db=self.db, tenant_id=self._tenant_id)
        invoice = await (
            await (
                await (
                    builder
                    .for_subscription(sub)
                    .add_lines()
                )
            ).apply_discount(sub.discount_id)
        ).apply_tax()

        return await invoice.build()

    # ── List / Get ───────────────────────────────────────────────

    async def list_invoices(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Invoice], int]:
        """List all invoices for the tenant (company view)."""
        invoices = await self._repo.find_all(
            offset=offset, limit=limit
        )
        total = await self._repo.count()
        return invoices, total

    async def get_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> Invoice:
        """Get a single invoice by ID."""
        return await self._repo.find_by_id(invoice_id)

    # ── Portal-specific ──────────────────────────────────────────

    async def list_invoices_for_customer(
        self,
        customer_id: uuid.UUID,
        *,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Invoice], int]:
        """List invoices scoped to a portal customer."""
        filters = [Invoice.customer_id == customer_id]

        if status:
            try:
                filters.append(Invoice.status == InvoiceStatus(status))
            except ValueError:
                pass
                
        if date_from:
            from datetime import date
            try:
                filters.append(Invoice.created_at >= date.fromisoformat(date_from[:10]))
            except ValueError:
                pass
                
        if date_to:
            from datetime import date
            try:
                filters.append(Invoice.created_at <= date.fromisoformat(date_to[:10]))
            except ValueError:
                pass

        invoices = await self._repo.find_all(
            filters=filters, offset=offset, limit=limit
        )
        total = await self._repo.count(*filters)
        return invoices, total

    async def get_invoice_for_customer(
        self,
        invoice_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Invoice:
        """Get single invoice ensuring portal ownership."""
        inv = await self._repo.find_by_id_for_customer(
            invoice_id, customer_id
        )
        if inv is None:
            raise NotFoundException("Invoice not found.")
        return inv

    # ── Lifecycle ────────────────────────────────────────────────

    async def confirm(self, invoice_id: uuid.UUID) -> Invoice:
        """Transition invoice from draft → confirmed."""
        inv = await self._repo.find_by_id(invoice_id)
        if inv.status != InvoiceStatus.DRAFT:
            raise ConflictException("Invoice is already confirmed.")
        return await self._repo.update(
            invoice_id, {"status": InvoiceStatus.CONFIRMED}
        )

    async def cancel(self, invoice_id: uuid.UUID) -> Invoice:
        """Cancel an invoice. Cannot cancel if payments exist."""
        inv = await self._repo.find_by_id(invoice_id)
        if inv.amount_paid > 0:
            raise ConflictException(
                "Cannot cancel — refund payment first."
            )
        if inv.status == InvoiceStatus.PAID:
            raise ConflictException(
                "Cannot cancel a paid invoice."
            )
        return await self._repo.update(
            invoice_id, {"status": InvoiceStatus.CANCELLED}
        )

    async def send(self, invoice_id: uuid.UUID) -> Invoice:
        """Mark invoice as sent (would trigger email in prod)."""
        inv = await self._repo.find_by_id(invoice_id)
        if inv.status != InvoiceStatus.CONFIRMED:
            raise ConflictException(
                "Only confirmed invoices can be sent."
            )
        # In production: Celery task send_invoice_email.delay(invoice_id)
        return inv

    async def update_invoice(
        self,
        invoice_id: uuid.UUID,
        data: dict,
    ) -> Invoice:
        """Partial update of invoice fields (due_date, etc.)."""
        inv = await self._repo.find_by_id(invoice_id)
        if inv.status not in (InvoiceStatus.DRAFT, InvoiceStatus.CONFIRMED):
            raise ConflictException(
                "Cannot update a paid or cancelled invoice."
            )
        return await self._repo.update(invoice_id, data)
