"""
Revenue recognition Celery tasks.

Tasks:
    process_revenue_recognition — triggered by invoice.confirmed event.
    process_pending_revenue     — hourly batch for unprocessed invoices.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


def process_revenue_recognition(
    invoice_id: str, tenant_id: str
):
    """Process revenue recognition for a single confirmed invoice."""
    async def _run():
        from uuid import UUID
        from app.core.database import async_session_factory
        from app.services.revenue.service import RevenueRecognitionService

        async with async_session_factory() as session:
            svc = RevenueRecognitionService(
                session, UUID(tenant_id)
            )
            count = await svc.process(UUID(invoice_id))
            logger.info(
                "Revenue recognition: %d rows for invoice %s",
                count,
                invoice_id,
            )
            await session.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()


def process_pending_revenue():
    """Hourly batch: process revenue for all confirmed invoices not yet recognized."""
    async def _run():
        from app.core.database import async_session_factory
        from app.core.enums import InvoiceStatus
        from app.models.invoice import Invoice
        from app.models.revenue_recognition import RevenueRecognition
        from app.services.revenue.service import RevenueRecognitionService
        from sqlalchemy import and_, select
        from uuid import UUID

        async with async_session_factory() as session:
            # Find confirmed invoices without recognition rows
            subquery = (
                select(RevenueRecognition.invoice_id)
                .distinct()
            )
            query = (
                select(Invoice)
                .where(
                    and_(
                        Invoice.status == InvoiceStatus.CONFIRMED,
                        Invoice.deleted_at.is_(None),
                        Invoice.id.notin_(subquery),
                    )
                )
            )
            result = await session.execute(query)
            invoices = result.scalars().all()

            for inv in invoices:
                try:
                    svc = RevenueRecognitionService(session, inv.tenant_id)
                    await svc.process(inv.id)
                except Exception as e:
                    logger.error(
                        "Revenue recognition failed for invoice %s: %s",
                        inv.id, e,
                    )

            await session.commit()
            logger.info(
                "Processed pending revenue for %d invoices",
                len(invoices),
            )

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()
