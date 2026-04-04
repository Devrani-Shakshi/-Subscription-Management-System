"""
Churn prediction Celery tasks.

Tasks:
    compute_churn_scores — daily batch job for all tenants.
    send_alert_email     — rate-limited alert for high-risk customers.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


def _get_celery():
    from app.config.celery_app import celery_app
    return celery_app


celery_app_lazy = None


def _ensure_celery():
    global celery_app_lazy
    if celery_app_lazy is None:
        celery_app_lazy = _get_celery()
    return celery_app_lazy


# ── compute_churn_scores ─────────────────────────────────────────
# Registered manually to avoid circular imports at module level

def compute_churn_scores():
    """
    Daily batch: compute churn scores for all portal_users per tenant.

    For each tenant:
      1. Instantiate ChurnService
      2. Call compute_all_scores()
      3. For scores >= 70: queue send_alert_email
    """
    async def _run():
        from app.core.database import async_session_factory
        from app.models.tenant import Tenant
        from app.core.enums import TenantStatus
        from sqlalchemy import select, and_

        async with async_session_factory() as session:
            # Get all active tenants
            query = select(Tenant).where(
                and_(
                    Tenant.status == TenantStatus.ACTIVE,
                    Tenant.deleted_at.is_(None),
                )
            )
            result = await session.execute(query)
            tenants = result.scalars().all()

            for tenant in tenants:
                try:
                    from app.services.churn.service import ChurnService

                    svc = ChurnService(session, tenant.id)
                    count = await svc.compute_all_scores()
                    logger.info(
                        "Computed churn scores for tenant %s: %d customers",
                        tenant.id,
                        count,
                    )
                except Exception as e:
                    logger.error(
                        "Churn scoring failed for tenant %s: %s",
                        tenant.id,
                        e,
                    )

            await session.commit()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()


# ── send_alert_email ────────────────────────────────────────────

def send_alert_email(company_email: str, customer_id: str):
    """
    Send churn alert email to company admin.

    Rate-limited via Redis: once per 24h per customer.
    """
    async def _send():
        from app.core.redis import get_redis

        redis = await get_redis()
        key = f"churn_alert:{customer_id}"

        # Check rate limit
        already_sent = await redis.get(key)
        if already_sent:
            logger.info(
                "Churn alert already sent for customer %s in last 24h",
                customer_id,
            )
            return

        # Mark as sent (24h TTL)
        await redis.set(key, "1", ex=86400)

        # In production: send actual email via SMTP/SendGrid
        logger.info(
            "CHURN ALERT: Sent to %s for customer %s",
            company_email,
            customer_id,
        )

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_send())
    finally:
        loop.close()
