"""
Central model registry — import every model here so Alembic
and SQLAlchemy's metadata.create_all discover them.
"""

from app.models.base import BaseModel  # noqa: F401 — DeclarativeBase
from app.models.tenant import Tenant  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.session import Session  # noqa: F401
from app.models.failed_login import FailedLoginAttempt  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.product_variant import ProductVariant  # noqa: F401
from app.models.plan import Plan  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.subscription_line import SubscriptionLine  # noqa: F401
from app.models.quotation_template import QuotationTemplate  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.invoice_line import InvoiceLine  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.discount import Discount  # noqa: F401
from app.models.tax import Tax  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.churn_score import ChurnScore  # noqa: F401
from app.models.dunning_schedule import DunningSchedule  # noqa: F401
from app.models.revenue_recognition import RevenueRecognition  # noqa: F401
from app.models.invite_token import InviteToken  # noqa: F401
