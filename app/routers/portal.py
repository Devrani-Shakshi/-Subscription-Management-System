"""
Portal router — portal_user only.

Endpoints:
  GET   /portal/me                       — current user profile
  GET   /portal/invoices                 — list own invoices
  GET   /portal/invoices/{id}            — get own invoice
  GET   /portal/invoices/{id}/pdf        — download own invoice PDF
  POST  /portal/invoices/{id}/pay        — pay an invoice
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.guards import (
    OwnershipGuard,
    get_tenant_session,
    require_portal_user,
)
from app.schemas.auth import TokenPayload
from app.schemas.billing import (
    InvoiceListResponse,
    InvoiceResponse,
    PaymentResponse,
    PortalPayRequest,
)
from app.services.billing.invoice_service import InvoiceService
from app.services.billing.payment_service import PaymentService
from app.services.billing.pdf_generator import InvoicePDFGenerator

router = APIRouter(
    prefix="/portal",
    tags=["portal"],
    dependencies=[Depends(require_portal_user)],
)


# ── Helpers ──────────────────────────────────────────────────────


def _invoice_to_response(inv) -> InvoiceResponse:
    """Map Invoice model to portal response schema."""
    return InvoiceResponse(
        id=inv.id,
        invoice_number=inv.invoice_number,
        subscription_id=inv.subscription_id,
        customer_id=inv.customer_id,
        status=inv.status,
        due_date=inv.due_date,
        subtotal=inv.subtotal,
        tax_total=inv.tax_total,
        discount_total=inv.discount_total,
        total=inv.total,
        amount_paid=inv.amount_paid,
        amount_due=inv.amount_due,
        discount_id=inv.discount_id,
        lines=[
            {
                "id": l.id,
                "product_id": l.product_id,
                "qty": l.qty,
                "unit_price": l.unit_price,
                "tax_id": l.tax_id,
                "discount_id": l.discount_id,
            }
            for l in (inv.lines or [])
        ],
        created_at=inv.created_at,
    )


def _payment_to_response(p) -> PaymentResponse:
    """Map Payment model to response schema."""
    return PaymentResponse(
        id=p.id,
        invoice_id=p.invoice_id,
        customer_id=p.customer_id,
        method=p.method,
        amount=p.amount,
        paid_at=p.paid_at,
        created_at=p.created_at,
    )


# ── Profile ──────────────────────────────────────────────────────


@router.get("/me")
async def get_me(
    user: TokenPayload = Depends(require_portal_user),
) -> dict:
    """Return authenticated portal_user profile."""
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
    }


# ═══════════════════════════════════════════════════════════════
# Invoice Endpoints (portal — read-only + pay)
# ═══════════════════════════════════════════════════════════════


@router.get("/invoices")
async def list_invoices(
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> InvoiceListResponse:
    """List invoices for the authenticated customer."""
    svc = InvoiceService(db, user.tenant_id)
    items, total = await svc.list_invoices_for_customer(
        user.user_id, offset=offset, limit=limit
    )
    return InvoiceListResponse(
        items=[_invoice_to_response(i) for i in items],
        total=total,
    )


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> InvoiceResponse:
    """Get a single invoice for the authenticated customer."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.get_invoice_for_customer(invoice_id, user.user_id)
    return _invoice_to_response(inv)


@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> Response:
    """Download invoice PDF (portal mode — no internal data)."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.get_invoice_for_customer(invoice_id, user.user_id)
    pdf = InvoicePDFGenerator().generate(inv, mode="portal")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{inv.invoice_number}.pdf"'
            )
        },
    )


@router.post("/invoices/{invoice_id}/pay")
async def pay_invoice(
    invoice_id: UUID,
    body: PortalPayRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> PaymentResponse:
    """Pay an invoice (full outstanding amount)."""
    svc = PaymentService(db, user.tenant_id)
    payment = await svc.portal_pay(
        invoice_id=invoice_id,
        customer_id=user.user_id,
        method=body.method,
    )
    return _payment_to_response(payment)
