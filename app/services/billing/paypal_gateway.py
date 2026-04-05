"""
PayPal Payment Gateway — async integration with PayPal REST API v2.

Uses httpx for non-blocking HTTP calls to PayPal's API.
Handles:
  - OAuth2 access token management
  - Order creation (checkout)
  - Order capture (after user approval)
  - Success / failure handling

⚠️ API Keys are configured in app/core/config.py via .env file:
    PAYPAL_CLIENT_ID=your-client-id
    PAYPAL_CLIENT_SECRET=your-secret-key
    PAYPAL_MODE=sandbox   (or "live" for production)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import settings
from app.core.enums import PayPalOrderStatus
from app.exceptions.base import (
    ConflictException,
    ServiceException,
    ValidationException,
)

logger = logging.getLogger(__name__)

# ── PayPal API base URLs ────────────────────────────────────────
_PAYPAL_BASE = {
    "sandbox": "https://api-m.sandbox.paypal.com",
    "live": "https://api-m.paypal.com",
}


class PayPalGateway:
    """
    Async PayPal REST API v2 client.

    Usage:
        gateway = PayPalGateway()
        order = await gateway.create_order(amount="99.99", currency="USD", ...)
        capture = await gateway.capture_order(order_id)
    """

    def __init__(self) -> None:
        self._client_id = settings.PAYPAL_CLIENT_ID
        self._client_secret = settings.PAYPAL_CLIENT_SECRET
        self._mode = settings.PAYPAL_MODE
        self._base_url = _PAYPAL_BASE.get(self._mode, _PAYPAL_BASE["sandbox"])
        self._success_url = settings.PAYPAL_SUCCESS_URL
        self._cancel_url = settings.PAYPAL_CANCEL_URL

        if not self._client_id or not self._client_secret:
            logger.warning(
                "PayPal credentials not configured. "
                "Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in .env"
            )

    # ── OAuth2 Access Token ─────────────────────────────────────

    async def _get_access_token(self) -> str:
        """Fetch OAuth2 bearer token from PayPal."""
        if not self._client_id or not self._client_secret:
            raise ServiceException(
                "PayPal API keys not configured. "
                "Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in .env"
            )

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/v1/oauth2/token",
                auth=(self._client_id, self._client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"},
            )

            if resp.status_code != 200:
                logger.error(f"PayPal auth failed: {resp.text}")
                raise ServiceException("PayPal authentication failed.")

            return resp.json()["access_token"]

    # ── Create Order ────────────────────────────────────────────

    async def create_order(
        self,
        *,
        amount: str,
        currency: str = "USD",
        invoice_id: str | None = None,
        description: str = "Subscription Payment",
        custom_id: str | None = None,
        success_url: str | None = None,
        cancel_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a PayPal order and return approval URL.

        Returns:
            {
                "order_id": "PAYPAL-ORDER-ID",
                "status": "CREATED",
                "approval_url": "https://www.sandbox.paypal.com/...",
            }
        """
        token = await self._get_access_token()

        order_payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": amount,
                    },
                    "description": description,
                }
            ],
            "application_context": {
                "return_url": success_url or self._success_url,
                "cancel_url": cancel_url or self._cancel_url,
                "brand_name": settings.APP_NAME,
                "landing_page": "LOGIN",
                "user_action": "PAY_NOW",
                "shipping_preference": "NO_SHIPPING",
            },
        }

        # Attach invoice reference if provided
        if invoice_id:
            order_payload["purchase_units"][0]["invoice_id"] = invoice_id
        if custom_id:
            order_payload["purchase_units"][0]["custom_id"] = custom_id

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/v2/checkout/orders",
                json=order_payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code not in (200, 201):
                logger.error(f"PayPal create order failed: {resp.text}")
                raise ServiceException(
                    f"PayPal order creation failed: {resp.json().get('message', 'Unknown error')}"
                )

            data = resp.json()
            approval_url = next(
                (
                    link["href"]
                    for link in data.get("links", [])
                    if link["rel"] == "approve"
                ),
                None,
            )

            logger.info(
                f"PayPal order created: {data['id']} | Amount: {amount} {currency}"
            )

            return {
                "order_id": data["id"],
                "status": data["status"],
                "approval_url": approval_url,
            }

    # ── Capture Order (after user approves) ─────────────────────

    async def capture_order(self, order_id: str) -> dict[str, Any]:
        """
        Capture payment after user approves on PayPal.

        This is the SUCCESS method — called when PayPal redirects
        back to your success URL.

        Returns:
            {
                "order_id": "...",
                "status": "COMPLETED",
                "payer_email": "buyer@example.com",
                "amount": "99.99",
                "currency": "USD",
                "capture_id": "...",
                "paid_at": "2026-04-05T...",
            }
        """
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code not in (200, 201):
                logger.error(f"PayPal capture failed: {resp.text}")
                raise ServiceException(
                    f"PayPal capture failed: {resp.json().get('message', 'Unknown error')}"
                )

            data = resp.json()
            capture = (
                data.get("purchase_units", [{}])[0]
                .get("payments", {})
                .get("captures", [{}])[0]
            )

            logger.info(
                f"PayPal payment captured: {order_id} | "
                f"Status: {data['status']}"
            )

            return {
                "order_id": data["id"],
                "status": data["status"],
                "payer_email": (
                    data.get("payer", {}).get("email_address", "")
                ),
                "amount": capture.get("amount", {}).get("value", "0"),
                "currency": capture.get("amount", {}).get(
                    "currency_code", "USD"
                ),
                "capture_id": capture.get("id", ""),
                "paid_at": capture.get(
                    "create_time",
                    datetime.now(timezone.utc).isoformat(),
                ),
            }

    # ── Get Order Details ───────────────────────────────────────

    async def get_order_details(self, order_id: str) -> dict[str, Any]:
        """Fetch current order status from PayPal."""
        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/v2/checkout/orders/{order_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            if resp.status_code != 200:
                logger.error(f"PayPal get order failed: {resp.text}")
                raise ServiceException("Failed to fetch PayPal order.")

            return resp.json()

    # ── Handle Failure ──────────────────────────────────────────

    @staticmethod
    def handle_failure(
        order_id: str,
        reason: str = "User cancelled or payment declined",
    ) -> dict[str, Any]:
        """
        Handle payment failure/cancellation.

        This is the FAILURE method — called when PayPal redirects
        to your cancel URL or payment is declined.
        """
        logger.warning(
            f"PayPal payment failed/cancelled: {order_id} | Reason: {reason}"
        )

        return {
            "order_id": order_id,
            "status": PayPalOrderStatus.FAILED.value,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
