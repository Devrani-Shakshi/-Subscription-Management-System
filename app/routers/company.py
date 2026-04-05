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
  POST   /company/invoices/{id}/paypal/checkout — initiate PayPal payment
  POST   /company/invoices/{id}/paypal/success  — handle PayPal success
  POST   /company/invoices/{id}/paypal/failure  — handle PayPal failure
  POST   /company/payments                  — record payment
  GET    /company/payments                  — list payments
  GET    /company/churn                     — churn score list
  GET    /company/revenue                   — revenue recognition timeline
  GET    /company/dashboard                 — health metrics
  GET    /company/audit                     — audit log
  GET    /company/audit/export              — audit CSV export
  POST   /company/subscriptions/bulk        — bulk subscription operations
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditAction, BulkOperationType
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
from app.schemas.advanced import (
    BulkOperationRequest,
    BulkOperationResponse,
    BulkPreviewResponse,
    ChurnScoreItem,
    ChurnScoreListResponse,
    CompanyAuditLogFilter,
    CompanyAuditLogResponse,
    CompanyDashboardResponse,
    MetricItem,
    RevenueTimelineItem,
    RevenueTimelineResponse,
)
from app.services.billing.invoice_service import InvoiceService
from app.services.billing.payment_service import PaymentService
from app.services.billing.paypal_service import PayPalPaymentService
from app.services.billing.pdf_generator import InvoicePDFGenerator
from app.services.tenant import TenantService
from app.schemas.paypal import (
    PayPalCheckoutRequest,
    PayPalCheckoutResponse,
    PayPalFailureRequest,
    PayPalFailureResponse,
    PayPalSuccessRequest,
    PayPalSuccessResponse,
)

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
# PayPal Payment Gateway
# ═══════════════════════════════════════════════════════════════


@router.post("/invoices/{invoice_id}/paypal/checkout")
async def paypal_checkout(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> PayPalCheckoutResponse:
    """Initiate PayPal checkout for an invoice."""
    svc = PayPalPaymentService(db, user.tenant_id)
    result = await svc.create_checkout(invoice_id=invoice_id)
    return PayPalCheckoutResponse(**result)


@router.post("/invoices/{invoice_id}/paypal/success")
async def paypal_success(
    invoice_id: UUID,
    body: PayPalSuccessRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> PayPalSuccessResponse:
    """Handle PayPal payment success — capture and record payment."""
    svc = PayPalPaymentService(db, user.tenant_id)
    result = await svc.handle_success(
        paypal_order_id=body.paypal_order_id,
        invoice_id=invoice_id,
    )
    return PayPalSuccessResponse(**result)


@router.post("/invoices/{invoice_id}/paypal/failure")
async def paypal_failure(
    invoice_id: UUID,
    body: PayPalFailureRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> PayPalFailureResponse:
    """Handle PayPal payment failure or cancellation."""
    svc = PayPalPaymentService(db, user.tenant_id)
    result = await svc.handle_failure(
        paypal_order_id=body.paypal_order_id,
        invoice_id=invoice_id,
        reason=body.reason or "Payment cancelled",
    )
    return PayPalFailureResponse(**result)


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


# ═══════════════════════════════════════════════════════════════
# Churn Prediction
# ═══════════════════════════════════════════════════════════════


@router.get("/churn", response_model=ChurnScoreListResponse)
async def list_churn_scores(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    min_score: Optional[int] = Query(None, ge=0, le=100),
) -> ChurnScoreListResponse:
    """List churn scores sorted by risk (highest first)."""
    from app.services.churn.service import ChurnService

    svc = ChurnService(db, user.tenant_id)
    items, total = await svc.list_churn_scores(
        offset=offset, limit=limit, min_score=min_score,
    )
    return ChurnScoreListResponse(
        items=[ChurnScoreItem(**item) for item in items],
        total=total,
    )


# ═══════════════════════════════════════════════════════════════
# Revenue Recognition
# ═══════════════════════════════════════════════════════════════


@router.get("/revenue", response_model=RevenueTimelineResponse)
async def get_revenue_timeline(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> RevenueTimelineResponse:
    """Revenue recognition timeline for this company."""
    from app.services.revenue.service import RevenueRecognitionService

    svc = RevenueRecognitionService(db, user.tenant_id)
    timeline = await svc.get_timeline()
    return RevenueTimelineResponse(
        timeline=[RevenueTimelineItem(**t) for t in timeline],
        total_recognized=str(
            sum(float(t["recognized"]) for t in timeline)
        ) if timeline else "0",
    )


# ═══════════════════════════════════════════════════════════════
# Health Dashboard
# ═══════════════════════════════════════════════════════════════


@router.get("/dashboard", response_model=CompanyDashboardResponse)
async def get_company_dashboard(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> CompanyDashboardResponse:
    """Health dashboard with KPI metrics."""
    from app.services.metrics.dashboard import DashboardService

    svc = DashboardService(db, user.tenant_id)
    raw = await svc.get_all()
    metrics = {
        k: MetricItem(name=k, **v) for k, v in raw.items()
    }
    return CompanyDashboardResponse(metrics=metrics)


# ═══════════════════════════════════════════════════════════════
# Audit Log (company-scoped)
# ═══════════════════════════════════════════════════════════════


@router.get("/audit", response_model=CompanyAuditLogResponse)
async def list_company_audit(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    entity_type: Optional[str] = Query(None),
    action: Optional[AuditAction] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> CompanyAuditLogResponse:
    """Filterable audit log for this company."""
    from app.services.company_audit import CompanyAuditService

    filters = CompanyAuditLogFilter(
        entity_type=entity_type,
        action=action,
        page=page,
        page_size=page_size,
    )
    svc = CompanyAuditService(db, user.tenant_id)
    return await svc.list_audit_logs(filters)


@router.get("/audit/export")
async def export_company_audit_csv(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    entity_type: Optional[str] = Query(None),
    action: Optional[AuditAction] = Query(None),
) -> StreamingResponse:
    """Export company audit log as CSV."""
    from app.services.company_audit import CompanyAuditService

    filters = CompanyAuditLogFilter(
        entity_type=entity_type,
        action=action,
    )
    svc = CompanyAuditService(db, user.tenant_id)
    csv_data = await svc.export_csv(filters)
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=audit_log.csv"
        },
    )


# ═══════════════════════════════════════════════════════════════
# Bulk Operations
# ═══════════════════════════════════════════════════════════════


@router.post("/subscriptions/bulk")
async def bulk_subscription_operation(
    body: BulkOperationRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> BulkPreviewResponse | BulkOperationResponse:
    """
    Bulk subscription operation.

    If confirm=False (default): returns conflict preview.
    If confirm=True: executes the operation and returns result.
    """
    from app.services.bulk.executor import BulkExecutor

    executor = BulkExecutor(db, user.tenant_id)

    if not body.confirm:
        preview = await executor.preview(
            ids=body.subscription_ids,
            operation_type=body.operation,
            params=body.params,
        )
        return BulkPreviewResponse(**preview)

    result = await executor.run(
        ids=body.subscription_ids,
        operation_type=body.operation,
        params=body.params,
        skip_ids=body.skip_ids,
    )
    return BulkOperationResponse(**result.to_dict())
