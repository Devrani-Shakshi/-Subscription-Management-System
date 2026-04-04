"""
Dashboard metrics Celery tasks.

Tasks:
    refresh_dashboard_cache — periodic cache warming for all active tenants.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


def refresh_dashboard_cache():
    """Periodically refresh dashboard metric caches for all tenants."""
    async def _run():
        from app.core.database import async_session_factory
        from app.core.enums import TenantStatus
        from app.models.tenant import Tenant
        from app.services.metrics.dashboard import DashboardService
        from sqlalchemy import and_, select

        async with async_session_factory() as session:
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
                    svc = DashboardService(session, tenant.id)
                    await svc.get_all()
                    logger.info(
                        "Refreshed dashboard cache for tenant %s",
                        tenant.id,
                    )
                except Exception as e:
                    logger.error(
                        "Dashboard cache refresh failed for %s: %s",
                        tenant.id, e,
                    )

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()
