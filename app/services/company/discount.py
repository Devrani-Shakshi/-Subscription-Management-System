"""
DiscountService — discount CRUD.

No additional business rules beyond schema-level validation.
"""

from __future__ import annotations

from app.models.discount import Discount
from app.services.company.base_entity import BaseEntityService


class DiscountService(BaseEntityService[Discount]):
    """Discount management for company role."""

    model = Discount
