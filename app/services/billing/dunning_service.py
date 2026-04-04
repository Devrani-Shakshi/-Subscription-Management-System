"""
Dunning Service — automated payment collection schedule + actions.

Responsibilities:
- Create dunning schedules from failed payments
- Execute dunning actions (retry, suspend, cancel)
- Factory pattern for action selection
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.dunning import DUNNING_SCHEDULE
from app.core.enums import (
    DunningAction,
    DunningStatus,
    InvoiceStatus,
    SubscriptionStatus,
)
from app.exceptions.base import ServiceException
from app.models.dunning_schedule import DunningSchedule
from app.models.invoice import Invoice
from app.repositories.billing import (
    DunningScheduleRepository,
    InvoiceRepository,
    SubscriptionRepository,
)
from app.services.base import BaseService


# ═══════════════════════════════════════════════════════════════
# Dunning Actions (Strategy / Factory pattern)
# ═══════════════════════════════════════════════════════════════


class BaseDunningAction(ABC):
    """Abstract dunning action."""

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._db = db
        self._tenant_id = tenant_id

    @abstractmethod
    async def execute(self, schedule: DunningSchedule) -> dict:
        """
        Execute the dunning action.

        Returns a result dict to store in result_json.
        """


class RetryAction(BaseDunningAction):
    """Attempt to charge the customer again."""

    async def execute(self, schedule: DunningSchedule) -> dict:
        inv_repo = InvoiceRepository(self._db, self._tenant_id)
        try:
            invoice = await inv_repo.find_by_id(schedule.invoice_id)
        except Exception:
            return {"status": "error", "reason": "Invoice not found"}

        # If already paid → skip
        if invoice.status == InvoiceStatus.PAID:
            schedule.status = DunningStatus.SKIPPED
            await self._db.flush()
            return {"status": "skipped", "reason": "Invoice already paid"}

        # In production: attempt charge via payment gateway
        # For now, simulate a retry result
        # On success: would create Payment, update invoice
        # On failure: mark schedule as failed
        schedule.status = DunningStatus.FAILED
        await self._db.flush()
        return {
            "status": "failed",
            "reason": "Payment gateway retry — simulated",
        }


class SuspendAction(BaseDunningAction):
    """Suspend the subscription (pause)."""

    async def execute(self, schedule: DunningSchedule) -> dict:
        inv_repo = InvoiceRepository(self._db, self._tenant_id)
        sub_repo = SubscriptionRepository(self._db, self._tenant_id)

        try:
            invoice = await inv_repo.find_by_id(schedule.invoice_id)
        except Exception:
            return {"status": "error", "reason": "Invoice not found"}

        if invoice.status == InvoiceStatus.PAID:
            schedule.status = DunningStatus.SKIPPED
            await self._db.flush()
            return {"status": "skipped", "reason": "Invoice already paid"}

        # Pause the subscription
        await sub_repo.update(
            invoice.subscription_id,
            {"status": SubscriptionStatus.PAUSED},
        )

        schedule.status = DunningStatus.SUCCESS
        await self._db.flush()

        # In production: Celery task send_email.delay(customer, 'paused')
        return {
            "status": "success",
            "action": "subscription_paused",
        }


class CancelAction(BaseDunningAction):
    """Cancel the subscription permanently."""

    async def execute(self, schedule: DunningSchedule) -> dict:
        inv_repo = InvoiceRepository(self._db, self._tenant_id)
        sub_repo = SubscriptionRepository(self._db, self._tenant_id)

        try:
            invoice = await inv_repo.find_by_id(schedule.invoice_id)
        except Exception:
            return {"status": "error", "reason": "Invoice not found"}

        if invoice.status == InvoiceStatus.PAID:
            schedule.status = DunningStatus.SKIPPED
            await self._db.flush()
            return {"status": "skipped", "reason": "Invoice already paid"}

        # Close the subscription
        await sub_repo.update(
            invoice.subscription_id,
            {"status": SubscriptionStatus.CLOSED},
        )

        schedule.status = DunningStatus.SUCCESS
        await self._db.flush()

        # In production: event_bus.emit('subscription.churned', sub)
        return {
            "status": "success",
            "action": "subscription_cancelled",
            "event": "subscription.churned",
        }


class DunningActionFactory:
    """Factory to create the correct dunning action handler."""

    _actions: dict[DunningAction, type[BaseDunningAction]] = {
        DunningAction.RETRY: RetryAction,
        DunningAction.SUSPEND: SuspendAction,
        DunningAction.CANCEL: CancelAction,
    }

    @staticmethod
    def create(
        action: DunningAction,
        db: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> BaseDunningAction:
        cls = DunningActionFactory._actions.get(action)
        if cls is None:
            raise ServiceException(
                f"Unknown dunning action: {action.value}"
            )
        return cls(db, tenant_id)


# ═══════════════════════════════════════════════════════════════
# Dunning Schedule Service
# ═══════════════════════════════════════════════════════════════


class DunningScheduleService(BaseService):
    """Manages dunning schedule lifecycle."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> None:
        super().__init__(db)
        self._tenant_id = tenant_id
        self._repo = DunningScheduleRepository(db, tenant_id)

    async def create_from_invoice(
        self,
        invoice: Invoice,
    ) -> list[DunningSchedule]:
        """
        Create dunning schedule rows from DUNNING_SCHEDULE config.

        Called when a payment fails.
        """
        schedules: list[DunningSchedule] = []
        base_time = datetime.now(timezone.utc)

        for idx, step in enumerate(DUNNING_SCHEDULE, start=1):
            schedule = await self._repo.create({
                "invoice_id": invoice.id,
                "attempt_number": idx,
                "action": step.action,
                "channel": step.channel,
                "scheduled_at": base_time + timedelta(days=step.day),
                "status": DunningStatus.PENDING,
                "result_json": {},
            })
            schedules.append(schedule)

        return schedules

    async def process_pending(self) -> list[dict]:
        """
        Process all pending dunning schedules that are due.

        Called by Celery beat task (hourly).
        """
        pending = await self._repo.find_pending_due()
        results: list[dict] = []

        for schedule in pending:
            action = DunningActionFactory.create(
                schedule.action, self.db, self._tenant_id
            )
            result = await action.execute(schedule)
            schedule.result_json = result
            await self.db.flush()
            results.append({
                "schedule_id": str(schedule.id),
                "action": schedule.action.value,
                "result": result,
            })

        return results

    async def list_by_invoice(
        self,
        invoice_id: uuid.UUID,
    ) -> Sequence[DunningSchedule]:
        """List all dunning schedules for an invoice."""
        return await self._repo.find_by_invoice(invoice_id)

    async def list_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[DunningSchedule], int]:
        """List all dunning schedules for the tenant."""
        schedules = await self._repo.find_all(
            offset=offset, limit=limit
        )
        total = await self._repo.count()
        return schedules, total
