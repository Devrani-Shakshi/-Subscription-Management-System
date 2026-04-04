"""
TaxService — tax rate CRUD.

No additional business rules beyond schema-level validation
(rate between 0 and 100).
"""

from __future__ import annotations

from app.models.tax import Tax
from app.services.company.base_entity import BaseEntityService


class TaxService(BaseEntityService[Tax]):
    """Tax management for company role."""

    model = Tax
