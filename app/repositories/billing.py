"""
Billing repositories — tenant-scoped data access for invoices,
payments, discounts, taxes, and dunning schedules.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import and_, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import DunningStatus, InvoiceStatus
from app.models.discount import Discount
from app.models.dunning_schedule import DunningSchedule
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.subscription_line import SubscriptionLine
from app.models.tax import Tax
from app.repositories.base import BaseRepository


# ═══════════════════════════════════════════════════════════════
# Invoice Repository
# ═══════════════════════════════════════════════════════════════


class InvoiceRepository(BaseRepository[Invoice]):
    model = Invoice

    async def find_by_customer(
        self,
        customer_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Invoice]:
        """List invoices for a specific customer (portal)."""
        return await self.find_all(
            filters=[Invoice.customer_id == customer_id],
            offset=offset,
            limit=limit,
        )

    async def find_by_id_for_customer(
        self,
        invoice_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Optional[Invoice]:
        """Find an invoice by ID scoped to a customer."""
        query = self._base_query().where(
            and_(
                Invoice.id == invoice_id,
                Invoice.customer_id == customer_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def next_number(self) -> str:
        """Generate the next invoice number for the tenant."""
        query = self._scope(
            select(sa_func.count()).select_from(Invoice)
        )
        result = await self.db.execute(query)
        count = result.scalar_one()
        return f"INV-{count + 1:06d}"

    async def count_by_status(
        self, status: InvoiceStatus
    ) -> int:
        return await self.count(Invoice.status == status)


# ═══════════════════════════════════════════════════════════════
# Payment Repository
# ═══════════════════════════════════════════════════════════════


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    async def find_by_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> Sequence[Payment]:
        return await self.find_all(
            filters=[Payment.invoice_id == invoice_id],
        )

    async def sum_by_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> float:
        """Sum all payments for an invoice."""
        query = self._scope(
            select(sa_func.coalesce(sa_func.sum(Payment.amount), 0))
            .select_from(Payment)
        ).where(Payment.invoice_id == invoice_id)
        result = await self.db.execute(query)
        return float(result.scalar_one())


# ═══════════════════════════════════════════════════════════════
# Subscription Repository
# ═══════════════════════════════════════════════════════════════


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription


# ═══════════════════════════════════════════════════════════════
# Subscription Line Repository
# ═══════════════════════════════════════════════════════════════


class SubscriptionLineRepository(BaseRepository[SubscriptionLine]):
    model = SubscriptionLine

    async def find_by_subscription(
        self,
        subscription_id: uuid.UUID,
    ) -> Sequence[SubscriptionLine]:
        return await self.find_all(
            filters=[SubscriptionLine.subscription_id == subscription_id],
        )


# ═══════════════════════════════════════════════════════════════
# Discount Repository
# ═══════════════════════════════════════════════════════════════


class DiscountRepository(BaseRepository[Discount]):
    model = Discount


# ═══════════════════════════════════════════════════════════════
# Tax Repository
# ═══════════════════════════════════════════════════════════════


class TaxRepository(BaseRepository[Tax]):
    model = Tax


# ═══════════════════════════════════════════════════════════════
# Dunning Schedule Repository
# ═══════════════════════════════════════════════════════════════


class DunningScheduleRepository(BaseRepository[DunningSchedule]):
    model = DunningSchedule

    async def find_pending_due(self) -> Sequence[DunningSchedule]:
        """Find all pending dunning schedules past their due time."""
        from datetime import datetime, timezone

        query = self._base_query().where(
            and_(
                DunningSchedule.status == DunningStatus.PENDING,
                DunningSchedule.scheduled_at <= datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def find_by_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> Sequence[DunningSchedule]:
        return await self.find_all(
            filters=[DunningSchedule.invoice_id == invoice_id],
        )

    async def count_by_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> int:
        return await self.count(
            DunningSchedule.invoice_id == invoice_id,
        )
