"""
Revenue recognition services — Strategy pattern implementations.

Strategies:
    RatableRecognitionStrategy   — splits evenly across billing periods
    MilestoneRecognitionStrategy — recognizes on specific dates
    RevenueRecognitionService    — orchestrator
"""

from app.services.revenue.strategies import (
    RecognitionStrategy,
    RatableRecognitionStrategy,
    MilestoneRecognitionStrategy,
)
from app.services.revenue.service import RevenueRecognitionService

__all__ = [
    "RecognitionStrategy",
    "RatableRecognitionStrategy",
    "MilestoneRecognitionStrategy",
    "RevenueRecognitionService",
]
