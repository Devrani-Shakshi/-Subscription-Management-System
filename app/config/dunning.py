"""
Dunning configuration — defines the escalation schedule.

This is the single source of truth for dunning behavior.
To change timing or actions, modify this list only.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import DunningAction


@dataclass(frozen=True)
class DunningStep:
    """One step in the dunning escalation."""
    day: int
    action: DunningAction
    channel: str


DUNNING_SCHEDULE: list[DunningStep] = [
    DunningStep(day=3,  action=DunningAction.RETRY,   channel="email"),
    DunningStep(day=7,  action=DunningAction.RETRY,   channel="email"),
    DunningStep(day=14, action=DunningAction.SUSPEND,  channel="email"),
    DunningStep(day=21, action=DunningAction.CANCEL,   channel="email"),
]
