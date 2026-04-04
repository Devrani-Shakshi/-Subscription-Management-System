"""
Health dashboard metrics — abstract MetricCalculator + concrete calculators.

Calculators:
    MRRCalculator       — Monthly Recurring Revenue
    ARRCalculator       — Annual Recurring Revenue
    NRRCalculator       — Net Revenue Retention
    ChurnRateCalculator — Customer churn rate
    LTVCalculator       — Customer Lifetime Value
    DashboardService    — aggregates all metrics with Redis caching
"""

from app.services.metrics.calculators import (
    MetricCalculator,
    MetricResult,
    DateRange,
    MRRCalculator,
    ARRCalculator,
    NRRCalculator,
    ChurnRateCalculator,
    LTVCalculator,
)
from app.services.metrics.dashboard import (
    DashboardService,
    SuperAdminMetricsDashboardService,
)

__all__ = [
    "MetricCalculator",
    "MetricResult",
    "DateRange",
    "MRRCalculator",
    "ARRCalculator",
    "NRRCalculator",
    "ChurnRateCalculator",
    "LTVCalculator",
    "DashboardService",
    "SuperAdminMetricsDashboardService",
]
