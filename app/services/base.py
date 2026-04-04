"""
Abstract base service — enforces OOP pattern across all services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService(ABC):
    """
    All domain services inherit from this.

    Subclasses must implement ``_get_repository`` to bind the
    appropriate tenant-scoped or super-admin repository.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
