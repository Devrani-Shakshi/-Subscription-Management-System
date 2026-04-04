"""
SubscriptionStatusFSM — finite state machine for subscription transitions.

Encapsulates the legal transition graph and guards.

TRANSITIONS = {
    'draft':     ['quotation'],
    'quotation': ['confirmed', 'draft'],
    'confirmed': ['active'],
    'active':    ['closed'],
    'closed':    []
}
"""

from __future__ import annotations

from app.core.enums import SubscriptionStatus
from app.exceptions.base import ConflictException
from app.models.subscription import Subscription


class SubscriptionStatusFSM:
    """Immutable FSM — all methods are static/class-level."""

    TRANSITIONS: dict[SubscriptionStatus, list[SubscriptionStatus]] = {
        SubscriptionStatus.DRAFT: [SubscriptionStatus.QUOTATION],
        SubscriptionStatus.QUOTATION: [
            SubscriptionStatus.CONFIRMED,
            SubscriptionStatus.DRAFT,
        ],
        SubscriptionStatus.CONFIRMED: [SubscriptionStatus.ACTIVE],
        SubscriptionStatus.ACTIVE: [SubscriptionStatus.CLOSED],
        SubscriptionStatus.CLOSED: [],
    }

    @classmethod
    def validate_transition(
        cls,
        current: SubscriptionStatus,
        target: SubscriptionStatus,
    ) -> None:
        """Raise ConflictException if transition is illegal."""
        allowed = cls.TRANSITIONS.get(current, [])
        if target not in allowed:
            raise ConflictException(
                f"Cannot move from {current.value} to {target.value}."
            )

    @classmethod
    def transition(
        cls,
        sub: Subscription,
        new_status: SubscriptionStatus,
    ) -> None:
        """
        Validate and apply transition in-place.

        Additional guards:
        - Cannot close if plan flags closable=False.
        """
        cls.validate_transition(sub.status, new_status)

        if new_status == SubscriptionStatus.CLOSED:
            cls._guard_closable(sub)

        sub.status = new_status

    @classmethod
    def _guard_closable(cls, sub: Subscription) -> None:
        """Block closure if the plan disallows it."""
        plan = getattr(sub, "plan", None)
        if plan is not None:
            flags = getattr(plan, "flags_json", {}) or {}
            if not flags.get("closable", True):
                raise ConflictException(
                    "This plan cannot be cancelled. Contact support."
                )
