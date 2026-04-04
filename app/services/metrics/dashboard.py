"""
Dashboard service — aggregates all metric calculators with Redis caching.

DashboardService: tenant-scoped (company role).
SuperAdminMetricsDashboardService: cross-tenant (super_admin role).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService
from app.services.metrics.calculators import (
    ARRCalculator,
    ChurnRateCalculator,
    DateRange,
    LTVCalculator,
    MetricCalculator,
    MetricResult,
    MRRCalculator,
    NRRCalculator,
)

logger = logging.getLogger(__name__)

# Cache TTL in seconds
_CACHE_TTL = 300


def _default_date_range() -> DateRange:
    """Default: last 30 days."""
    end = date.today()
    start = end - timedelta(days=30)
    return DateRange(start=start, end=end)


class DashboardService(BaseService):
    """Tenant-scoped dashboard metrics with Redis caching."""

    def __init__(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        date_range: DateRange | None = None,
    ) -> None:
        super().__init__(db)
        self.tenant_id = tenant_id
        self.date_range = date_range or _default_date_range()

    def _get_calculators(self) -> list[MetricCalculator]:
        """Build calculator instances for this tenant."""
        args = (self.db, self.tenant_id, self.date_range)
        return [
            MRRCalculator(*args),
            ARRCalculator(*args),
            NRRCalculator(*args),
            ChurnRateCalculator(*args),
            LTVCalculator(*args),
        ]

    async def get_all(self) -> dict[str, Any]:
        """
        Compute all metrics, try cache first.

        Cache key: metric:{name}:{tenant_id}:{date_range}
        """
        cache_key = (
            f"dashboard:{self.tenant_id}:"
            f"{self.date_range.start}:{self.date_range.end}"
        )

        # Try cache
        cached = await self._get_cache(cache_key)
        if cached is not None:
            return cached

        # Compute
        results: dict[str, Any] = {}
        for calc in self._get_calculators():
            try:
                result = await calc.calculate()
                results[result.name] = {
                    "value": result.value,
                    "raw_value": str(result.raw_value),
                    "trend": result.trend,
                    "delta": result.delta,
                    "period": result.period,
                }
            except Exception as e:
                logger.warning("Calculator %s failed: %s", calc.__class__.__name__, e)
                results[calc.__class__.__name__] = {
                    "value": "N/A",
                    "raw_value": "0",
                    "error": str(e),
                }

        # Cache result
        await self._set_cache(cache_key, results)
        return results

    async def _get_cache(self, key: str) -> dict | None:
        """Retrieve from Redis cache."""
        try:
            from app.core.redis import get_redis
            redis = await get_redis()
            data = await redis.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass  # Cache miss is fine
        return None

    async def _set_cache(self, key: str, data: dict) -> None:
        """Store in Redis cache with TTL."""
        try:
            from app.core.redis import get_redis
            redis = await get_redis()
            await redis.set(key, json.dumps(data), ex=_CACHE_TTL)
        except Exception:
            pass  # Cache write failure is fine


class SuperAdminMetricsDashboardService(DashboardService):
    """
    Cross-tenant dashboard — no tenant filter.

    Injects tenant_id=None into calculators so they aggregate globally.
    """

    def __init__(
        self,
        db: AsyncSession,
        date_range: DateRange | None = None,
    ) -> None:
        # Skip DashboardService.__init__ to avoid requiring tenant_id
        BaseService.__init__(self, db)
        self.tenant_id = None  # type: ignore[assignment]
        self.date_range = date_range or _default_date_range()

    def _get_calculators(self) -> list[MetricCalculator]:
        """Build calculator instances without tenant filter."""
        args = (self.db, None, self.date_range)
        return [
            MRRCalculator(*args),
            ARRCalculator(*args),
            NRRCalculator(*args),
            ChurnRateCalculator(*args),
            LTVCalculator(*args),
        ]
