"""
Subscription services — domain logic for subscription lifecycle.

Services:
    SubscriptionFSM         — state machine for subscription transitions
    SubscriptionService     — company CRUD + multi-step creation
    UpgradeService          — pro-rata upgrade logic
    DowngradeService        — scheduled downgrade logic
    PortalSubscriptionSvc   — portal_user self-service
    ProRataCalculator       — billing day calculations
    InvoiceFactory          — invoice creation (Factory pattern)
"""

from app.services.subscriptions.fsm import SubscriptionStatusFSM
from app.services.subscriptions.subscription import SubscriptionService
from app.services.subscriptions.upgrade import UpgradeService
from app.services.subscriptions.downgrade import DowngradeService
from app.services.subscriptions.portal import PortalSubscriptionService
from app.services.subscriptions.pro_rata import ProRataCalculator
from app.services.subscriptions.invoice_factory import InvoiceFactory

__all__ = [
    "SubscriptionStatusFSM",
    "SubscriptionService",
    "UpgradeService",
    "DowngradeService",
    "PortalSubscriptionService",
    "ProRataCalculator",
    "InvoiceFactory",
]
