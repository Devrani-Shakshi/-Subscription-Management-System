"""
PayPal Pydantic v2 schemas — request/response models for PayPal endpoints.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
# Request Schemas
# ═══════════════════════════════════════════════════════════════


class PayPalCheckoutRequest(BaseModel):
    """Request to initiate PayPal checkout for an invoice."""
    invoice_id: UUID


class PayPalSuccessRequest(BaseModel):
    """Request when PayPal redirects back after successful approval."""
    paypal_order_id: str = Field(
        ..., min_length=1, description="PayPal Order ID from redirect"
    )
    invoice_id: UUID


class PayPalFailureRequest(BaseModel):
    """Request when PayPal payment is cancelled or declined."""
    paypal_order_id: str = Field(
        ..., min_length=1, description="PayPal Order ID"
    )
    invoice_id: UUID
    reason: Optional[str] = Field(
        "Payment cancelled by user",
        max_length=500,
    )


# ═══════════════════════════════════════════════════════════════
# Response Schemas
# ═══════════════════════════════════════════════════════════════


class PayPalCheckoutResponse(BaseModel):
    """Response after creating a PayPal checkout order."""
    paypal_order_id: str
    approval_url: Optional[str]
    invoice_id: str
    amount: str
    status: str


class PayPalSuccessResponse(BaseModel):
    """Response after successfully capturing a PayPal payment."""
    status: str
    paypal_order_id: str
    capture_id: str
    payment_id: str
    amount_paid: str
    invoice_status: str
    payer_email: Optional[str] = ""


class PayPalFailureResponse(BaseModel):
    """Response for a failed/cancelled PayPal payment."""
    status: str
    paypal_order_id: str
    invoice_id: str
    reason: str
    timestamp: str
