"""
Company services — domain logic for the company role.

Each service extends BaseEntityService[T] for DRY CRUD operations.
"""

from app.services.company.base_entity import BaseEntityService
from app.services.company.product import ProductService
from app.services.company.plan import PlanService
from app.services.company.customer import CustomerService
from app.services.company.template import TemplateService
from app.services.company.discount import DiscountService
from app.services.company.tax import TaxService

__all__ = [
    "BaseEntityService",
    "ProductService",
    "PlanService",
    "CustomerService",
    "TemplateService",
    "DiscountService",
    "TaxService",
]
