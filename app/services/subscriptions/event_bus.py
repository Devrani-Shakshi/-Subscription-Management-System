"""
Simple in-process event bus — decouples side-effects from core logic.

Usage:
    event_bus.emit('subscription.upgraded', sub)
    event_bus.on('subscription.upgraded', my_handler)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventBus:
    """Lightweight sync event bus for domain events."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Any]]] = defaultdict(
            list
        )

    def on(self, event_name: str, handler: Callable[..., Any]) -> None:
        """Register a handler for an event."""
        self._handlers[event_name].append(handler)

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """Fire all handlers for an event. Errors are logged, not raised."""
        for handler in self._handlers.get(event_name, []):
            try:
                handler(*args, **kwargs)
            except Exception:
                logger.exception(
                    "Event handler error: %s -> %s",
                    event_name,
                    handler.__name__,
                )


# Singleton instance
event_bus = EventBus()
