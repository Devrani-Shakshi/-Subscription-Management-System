"""
Churn prediction signals + scoring engine.

Services:
    ChurnSignal (ABC)           — base signal interface
    LoginInactivitySignal       — days since last login
    OverdueInvoiceSignal        — overdue invoice count
    DowngradeSignal             — recent downgrades
    PausedSignal                — paused subscription
    DunningSignal               — active dunning schedule
    ChurnScoreEngine            — aggregate scorer
    ChurnService                — tenant-scoped churn API
"""

from app.services.churn.signals import (
    ChurnSignal,
    SignalResult,
    LoginInactivitySignal,
    OverdueInvoiceSignal,
    DowngradeSignal,
    PausedSignal,
    DunningSignal,
)
from app.services.churn.engine import ChurnScoreEngine
from app.services.churn.service import ChurnService

__all__ = [
    "ChurnSignal",
    "SignalResult",
    "LoginInactivitySignal",
    "OverdueInvoiceSignal",
    "DowngradeSignal",
    "PausedSignal",
    "DunningSignal",
    "ChurnScoreEngine",
    "ChurnService",
]
