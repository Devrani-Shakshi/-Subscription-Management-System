"""
Company router — company role only.

Endpoints:
  POST   /company/customers/invite         — invite portal_user
  GET    /company/invoices                  — list invoices
  POST   /company/invoices                  — generate invoice from subscription
  GET    /company/invoices/{id}             — get invoice detail
  PATCH  /company/invoices/{id}             — update invoice
  POST   /company/invoices/{id}/confirm     — confirm invoice
  POST   /company/invoices/{id}/cancel      — cancel invoice
  POST   /company/invoices/{id}/send        — send invoice
  GET    /company/invoices/{id}/pdf         — download invoice PDF
  POST   /company/invoices/bulk-send        — bulk send invoices
  POST   /company/payments                  — record payment
  GET    /company/payments                  — list payments
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.guards import get_tenant_session, require_company
from app.schemas.auth import InviteCustomerSchema, TokenPayload
from app.schemas.billing import (
    InvoiceBulkSendRequest,
    InvoiceGenerateRequest,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdateRequest,
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentResponse,
)
from app.services.billing.invoice_service import InvoiceService
from app.services.billing.payment_service import PaymentService
from app.services.billing.pdf_generator import InvoicePDFGenerator
from app.services.tenant import TenantService

router = APIRouter(
    prefix="/company",
    tags=["company"],
    dependencies=[Depends(require_company)],
)


# ── Helpers ──────────────────────────────────────────────────────


def _invoice_to_response(inv) -> InvoiceResponse:
    """Map Invoice model to response schema."""
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


# ── Customer invite ─────────────────────────────────────────────


@router.post("/customers/invite", status_code=201)
async def invite_customer(
    body: InviteCustomerSchema,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Invite a portal_user customer."""
    svc = TenantService(db)
    return await svc.invite_customer(body, tenant_id=user.tenant_id)


# ═══════════════════════════════════════════════════════════════
# Invoice Endpoints
# ═══════════════════════════════════════════════════════════════


@router.get("/invoices")
async def list_invoices(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> InvoiceListResponse:
    """List all invoices for the company."""
    svc = InvoiceService(db, user.tenant_id)
    items, total = await svc.list_invoices(offset=offset, limit=limit)
    return InvoiceListResponse(
        items=[_invoice_to_response(i) for i in items],
        total=total,
    )


@router.post("/invoices", status_code=201)
async def create_invoice(
    body: InvoiceGenerateRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> InvoiceResponse:
    """Generate a draft invoice from a subscription."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.generate_from_subscription(body.subscription_id)
    return _invoice_to_response(inv)


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> InvoiceResponse:
    """Get a single invoice by ID."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.get_invoice(invoice_id)
    return _invoice_to_response(inv)


@router.patch("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: UUID,
    body: InvoiceUpdateRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> InvoiceResponse:
    """Update invoice fields (due_date, etc.)."""
    svc = InvoiceService(db, user.tenant_id)
    data = body.model_dump(exclude_none=True)
    inv = await svc.update_invoice(invoice_id, data)
    return _invoice_to_response(inv)


@router.post("/invoices/{invoice_id}/confirm")
async def confirm_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> InvoiceResponse:
    """Confirm a draft invoice."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.confirm(invoice_id)
    return _invoice_to_response(inv)


@router.post("/invoices/{invoice_id}/cancel")
async def cancel_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> InvoiceResponse:
    """Cancel an invoice."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.cancel(invoice_id)
    return _invoice_to_response(inv)


@router.post("/invoices/{invoice_id}/send")
async def send_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> InvoiceResponse:
    """Send a confirmed invoice to the customer."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.send(invoice_id)
    return _invoice_to_response(inv)


@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> Response:
    """Download invoice PDF (internal mode for company)."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.get_invoice(invoice_id)
    pdf = InvoicePDFGenerator().generate(inv, mode="internal")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{inv.invoice_number}.pdf"'
            )
        },
    )


@router.post("/invoices/bulk-send")
async def bulk_send_invoices(
    body: InvoiceBulkSendRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Bulk send confirmed invoices."""
    svc = InvoiceService(db, user.tenant_id)
    sent = []
    for inv_id in body.invoice_ids:
        inv = await svc.send(inv_id)
        sent.append(str(inv.id))
    return {"sent": sent, "count": len(sent)}


# ═══════════════════════════════════════════════════════════════
# Payment Endpoints
# ═══════════════════════════════════════════════════════════════


@router.post("/payments", status_code=201)
async def record_payment(
    body: PaymentCreateRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> PaymentResponse:
    """Record a manual payment against an invoice."""
    svc = PaymentService(db, user.tenant_id)
    payment = await svc.record_payment(
        invoice_id=body.invoice_id,
        amount=body.amount,
        method=body.method,
        paid_at=body.paid_at,
    )
    return _payment_to_response(payment)


@router.get("/payments")
async def list_payments(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> PaymentListResponse:
    """List all payments for the company."""
    svc = PaymentService(db, user.tenant_id)
    items, total = await svc.list_payments(offset=offset, limit=limit)
    return PaymentListResponse(
        items=[_payment_to_response(p) for p in items],
        total=total,
    )
