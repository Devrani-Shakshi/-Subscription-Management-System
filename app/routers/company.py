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

from decimal import Decimal
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
    PaymentSummary,
    UnpaidInvoiceOption,
    DiscountResponse,
    DiscountListResponse,
    DiscountCreateRequest,
    TaxResponse,
    TaxListResponse,
    TaxCreateRequest,
    TemplateResponse,
    TemplateListResponse,
    TemplateCreateRequest,
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
    """Map Invoice model to response schema with display names."""
    from app.schemas.billing import InvoiceResponse, InvoiceLineResponse

    return InvoiceResponse(
        id=inv.id,
        number=inv.invoice_number,
        subscription_id=inv.subscription_id,
        customer_id=inv.customer_id,
        subscriptionName=inv.subscription.number if inv.subscription else "Unknown",
        customerName=inv.customer.name if inv.customer else "Unknown",
        customerEmail=inv.customer.email if inv.customer else "",
        customerAddress="",
        status=inv.status,
        invoiceDate=inv.created_at,
        dueDate=inv.due_date,
        subtotal=inv.subtotal,
        taxTotal=inv.tax_total,
        discountTotal=inv.discount_total,
        total=inv.total,
        amountPaid=inv.amount_paid,
        amountDue=inv.amount_due,
        createdAt=inv.created_at,
        updatedAt=inv.created_at,
        lineItems=[
            InvoiceLineResponse(
                id=l.id,
                product_id=l.product_id,
                product=l.product.name if l.product else "Unknown Product",
                description=l.product.description if l.product and hasattr(l.product, "description") else "",
                quantity=l.qty,
                unitPrice=l.unit_price,
                taxPercent=0.0,  # Placeholder for tax logic
                discount=Decimal("0"), # Placeholder for discount logic
                amount=l.qty * l.unit_price
            )
            for l in (inv.lines or [])
        ],
    )


def _payment_to_response(p) -> PaymentResponse:
    """Map Payment model to response schema."""
    return PaymentResponse(
        id=p.id,
        invoiceId=p.invoice_id,
        invoiceNumber=p.invoice.invoice_number if p.invoice else "Unknown",
        customerId=p.customer_id,
        customerName=p.customer.name if p.customer else "Unknown",
        method=p.method,
        amount=p.amount,
        date=p.paid_at,
        createdAt=p.created_at,
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
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
) -> InvoiceListResponse:
    """List all invoices for the company."""
    real_offset = offset if offset is not None else (page - 1) * limit
    svc = InvoiceService(db, user.tenant_id)
    items, total = await svc.list_invoices(offset=real_offset, limit=limit)
    return InvoiceListResponse(
        data=[_invoice_to_response(i) for i in items],
        meta={
            "total": total,
            "page": page,
            "limit": limit
        },
    )


@router.post("/invoices", status_code=201)
async def create_invoice(
    body: InvoiceGenerateRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Generate a draft invoice from a subscription."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.generate_from_subscription(body.subscription_id)
    return {"data": _invoice_to_response(inv)}


@router.get("/invoices/unpaid")
async def list_unpaid_invoices(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    search: Optional[str] = Query(None),
) -> dict:
    """List manual payment candidates (confirmed/overdue with amount_due > 0)."""
    from sqlalchemy import select, or_
    from app.models.invoice import Invoice
    from app.core.enums import InvoiceStatus

    q = select(Invoice).where(
        Invoice.tenant_id == user.tenant_id,
        Invoice.status.in_([InvoiceStatus.CONFIRMED, InvoiceStatus.OVERDUE]),
        (Invoice.total - Invoice.amount_paid) > 0
    )
    
    if search:
        q = q.where(Invoice.invoice_number.ilike(f"%{search}%"))

    res = await db.execute(q)
    items = res.scalars().all()
    
    return {
        "data": [
            UnpaidInvoiceOption(
                id=i.id,
                number=i.invoice_number,
                customerName=i.customer.name if i.customer else "Unknown",
                total=i.total,
                amountDue=i.amount_due,
                isOverdue=(i.status == InvoiceStatus.OVERDUE)
            ) for i in items
        ]
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Get a single invoice by ID."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.get_invoice(invoice_id)
    return {"data": _invoice_to_response(inv)}


@router.patch("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: UUID,
    body: InvoiceUpdateRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Update invoice fields (due_date, etc.)."""
    svc = InvoiceService(db, user.tenant_id)
    data = body.model_dump(exclude_none=True)
    inv = await svc.update_invoice(invoice_id, data)
    return {"data": _invoice_to_response(inv)}


@router.post("/invoices/{invoice_id}/confirm")
async def confirm_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Confirm a draft invoice."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.confirm(invoice_id)
    return {"data": _invoice_to_response(inv)}


@router.post("/invoices/{invoice_id}/cancel")
async def cancel_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Cancel an invoice."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.cancel(invoice_id)
    return {"data": _invoice_to_response(inv)}


@router.post("/invoices/{invoice_id}/send")
async def send_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Send a confirmed invoice to the customer."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.send(invoice_id)
    # Backend send() doesn't currently store who it was sent to,
    # but the frontend expects res.data.email
    return {
        "data": {
            **_invoice_to_response(inv).model_dump(),
            "email": inv.customer.email if inv.customer else "customer@example.com"
        }
    }


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
        paid_at=body.date,
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
        data=[_payment_to_response(p) for p in items],
        meta={
            "total": total,
            "page": (offset // limit) + 1,
            "limit": limit
        },
    )


@router.get("/payments/summary")
async def get_payment_summary(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Aggregated financial summary (tenant-wide)."""
    from sqlalchemy import select, func, or_
    from app.models.invoice import Invoice
    from app.models.payment import Payment
    from app.core.enums import InvoiceStatus

    # Total Received
    reveived_q = select(func.sum(Payment.amount)).where(Payment.tenant_id == user.tenant_id)
    received_res = await db.execute(reveived_q)
    total_received = received_res.scalar() or Decimal("0")

    # Outstanding (confirmed/partial)
    outstanding_q = select(func.sum(Invoice.total - Invoice.amount_paid)).where(
        Invoice.tenant_id == user.tenant_id,
        Invoice.status == InvoiceStatus.CONFIRMED
    )
    outstanding_res = await db.execute(outstanding_q)
    total_outstanding = outstanding_res.scalar() or Decimal("0")

    # Overdue
    overdue_q = select(func.sum(Invoice.total - Invoice.amount_paid)).where(
        Invoice.tenant_id == user.tenant_id,
        Invoice.status == InvoiceStatus.OVERDUE
    )
    overdue_res = await db.execute(overdue_q)
    total_overdue = overdue_res.scalar() or Decimal("0")

    return {
        "data": PaymentSummary(
            totalReceived=total_received,
            outstanding=total_outstanding,
            overdue=total_overdue
        )
    }


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
    from sqlalchemy import select, func
    from app.services.metrics.dashboard import DashboardService
    from app.models.subscription import Subscription
    from app.models.invoice import Invoice
    from app.services.company_audit import CompanyAuditService
    from app.schemas.advanced import CompanyAuditLogFilter
    from app.services.churn.service import ChurnService

    # Base Core Metrics
    svc = DashboardService(db, user.tenant_id)
    raw_metrics = await svc.get_all()
    
    from app.core.enums import SubscriptionStatus, InvoiceStatus
    # Missing extra metrics
    subs_q = await db.execute(select(func.count(Subscription.id)).where(
        Subscription.tenant_id == user.tenant_id, Subscription.status == SubscriptionStatus.ACTIVE
    ))
    subs_count = subs_q.scalar() or 0
    raw_metrics["active_subscriptions"] = {
        "value": str(subs_count), "raw_value": str(subs_count), "trend": "flat", "delta": "0", "period": ""
    }
    
    inv_q = await db.execute(select(func.count(Invoice.id)).where(
        Invoice.tenant_id == user.tenant_id, Invoice.status == InvoiceStatus.OVERDUE
    ))
    inv_count = inv_q.scalar() or 0
    raw_metrics["overdue_invoices"] = {
        "value": str(inv_count), "raw_value": str(inv_count), "trend": "flat", "delta": "0", "period": ""
    }

    metrics = {k.lower(): MetricItem(name=k, **v) for k, v in raw_metrics.items()}
    
    # Recent Activity
    audit_svc = CompanyAuditService(db, user.tenant_id)
    audit_res = await audit_svc.list_audit_logs(CompanyAuditLogFilter(page=1, page_size=10))
    recent_activity = [
        {
            "id": str(i.id),
            "entity_type": i.entity_type,
            "action": i.action.value,
            "entity_id": str(i.entity_id),
            "description": f"{i.actor_name or 'System'} {i.action.value} {i.entity_type}",
            "created_at": i.created_at.isoformat()
        } for i in audit_res.items
    ]
    
    # At Risk Customers
    churn_svc = ChurnService(db, user.tenant_id)
    churn_items, _ = await churn_svc.list_churn_scores(limit=5)
    at_risk = [
        {
            "id": str(i["customer_id"]),
            "name": i["customer_name"],
            "email": i["customer_email"],
            "score": i["score"],
            "risk_level": i["risk_level"]
        } for i in churn_items if i["risk_level"] in ("high", "medium")
    ]
    
    # Active Dunning
    from app.models.dunning_schedule import DunningSchedule
    from sqlalchemy.orm import selectinload
    from app.core.enums import DunningStatus
    dunning_q = await db.execute(
        select(DunningSchedule).options(selectinload(DunningSchedule.invoice))
        .where(DunningSchedule.tenant_id == user.tenant_id, DunningSchedule.status == DunningStatus.PENDING)
        .limit(5)
    )
    active_dunning = [
        {
            "id": str(d.id),
            "invoice_number": d.invoice.invoice_number if d.invoice else "Unknown",
            "customer_name": "Customer", # Mocking name since join is deeper
            "attempt": d.attempt_number,
            "next_retry": d.scheduled_at.isoformat(),
            "status": d.status.value
        } for d in dunning_q.scalars().all()
    ]
    
    # Mocks for charts until historical pipelines run
    v = float(raw_metrics.get("MRR", {}).get("raw_value", 0))
    mrr_chart = [
        {"month": "Jan", "mrr": max(0, int(v - 100))},
        {"month": "Feb", "mrr": max(0, int(v - 50))},
        {"month": "Mar", "mrr": max(0, int(v - 20))},
        {"month": "Apr", "mrr": int(v)},
    ]
    subs_chart = [
        {"month": "Jan", "count": max(0, int(subs_count - 2))},
        {"month": "Feb", "count": max(0, int(subs_count - 1))},
        {"month": "Mar", "count": max(0, int(subs_count))},
        {"month": "Apr", "count": int(subs_count)},
    ]

    return CompanyDashboardResponse(
        metrics=metrics,
        recent_activity=recent_activity,
        at_risk_customers=at_risk,
        active_dunning=active_dunning,
        mrr_chart=mrr_chart,
        subscriptions_chart=subs_chart,
    )


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


# ═══════════════════════════════════════════════════════════════
# Product CRUD
# ═══════════════════════════════════════════════════════════════


@router.get("/products")
async def list_products(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> dict:
    """List all products for the company."""
    from sqlalchemy import select, func
    from app.models.product import Product

    base = select(Product).where(Product.tenant_id == user.tenant_id)
    total_q = await db.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = total_q.scalar() or 0

    result = await db.execute(
        base.order_by(Product.created_at.desc()).offset(offset).limit(limit)
    )
    items = result.scalars().all()

    return {
        "data": [
            {
                "id": str(p.id),
                "name": p.name,
                "type": p.type,
                "sales_price": float(p.sales_price),
                "cost_price": float(p.cost_price),
                "variants": [
                    {
                        "id": str(v.id), 
                        "attribute": v.attribute, 
                        "value": v.value, 
                        "extra_price": float(v.extra_price)
                    } for v in p.variants
                ] if p.variants else [],
                "created_at": p.created_at.isoformat() if p.created_at else "",
            }
            for p in items
        ],
        "meta": {"total": total, "page": (offset // limit) + 1, "limit": limit},
    }


@router.post("/products", status_code=201)
async def create_product(
    body: dict,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Create a new product."""
    from decimal import Decimal
    from app.models.product import Product

    product = Product(
        tenant_id=user.tenant_id,
        name=body["name"],
        type=body.get("type", "service"),
        sales_price=Decimal(str(body.get("salesPrice", 0))),
        cost_price=Decimal(str(body.get("costPrice", 0))),
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)

    return {
        "id": str(product.id),
        "name": product.name,
        "type": product.type,
        "salesPrice": float(product.sales_price),
        "costPrice": float(product.cost_price),
    }


@router.put("/products/{product_id}")
async def update_product(
    product_id: UUID,
    body: dict,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Update a product."""
    from decimal import Decimal
    from sqlalchemy import select
    from app.models.product import Product
    from app.exceptions.base import NotFoundException

    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == user.tenant_id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException("Product not found.")

    if "name" in body:
        product.name = body["name"]
    if "type" in body:
        product.type = body["type"]
    if "salesPrice" in body:
        product.sales_price = Decimal(str(body["salesPrice"]))
    if "costPrice" in body:
        product.cost_price = Decimal(str(body["costPrice"]))

    await db.flush()
    await db.refresh(product)

    return {
        "id": str(product.id),
        "name": product.name,
        "type": product.type,
        "salesPrice": float(product.sales_price),
        "costPrice": float(product.cost_price),
    }


@router.delete("/products/{product_id}", status_code=204, response_class=Response)
async def delete_product(
    product_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> Response:
    """Delete a product (fails if used in active subscriptions)."""
    from sqlalchemy import select, func
    from app.models.product import Product
    from app.models.subscription_line import SubscriptionLine
    from app.exceptions.base import ConflictException, NotFoundException

    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == user.tenant_id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundException("Product not found.")

    # Check if used in subscription lines
    usage = await db.execute(
        select(func.count()).where(SubscriptionLine.product_id == product_id)
    )
    if (usage.scalar() or 0) > 0:
        raise ConflictException("Product is used in active subscriptions.")

    await db.delete(product)
    await db.flush()
    return Response(status_code=204)


# ═══════════════════════════════════════════════════════════════
# Plan CRUD
# ═══════════════════════════════════════════════════════════════


@router.get("/plans")
async def list_plans(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
) -> dict:
    """List all plans for the company."""
    from sqlalchemy import select, func
    from app.models.plan import Plan

    base = select(Plan).where(Plan.tenant_id == user.tenant_id)

    # Filter active plans (end_date is null or in the future)
    if status == "active":
        from datetime import date as dt_date
        base = base.where(
            (Plan.end_date.is_(None)) | (Plan.end_date >= dt_date.today())
        )

    # Subquery for subscription count
    from app.models.subscription import Subscription
    sub_count_q = (
        select(func.count(Subscription.id))
        .where(Subscription.plan_id == Plan.id)
        .scalar_subquery()
    )

    # Total count for pagination
    from sqlalchemy import func
    total_res = await db.execute(
        select(func.count(Plan.id)).where(Plan.tenant_id == user.tenant_id)
    )
    total = total_res.scalar() or 0

    result = await db.execute(
        select(Plan, sub_count_q.label("subs_count"))
        .where(Plan.tenant_id == user.tenant_id)
        .order_by(Plan.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()

    return {
        "data": [
            {
                "id": str(p.id),
                "name": p.name,
                "price": float(p.price),
                "billingPeriod": p.billing_period.value,
                "minQty": p.min_qty,
                "startDate": p.start_date.isoformat() if p.start_date else None,
                "endDate": p.end_date.isoformat() if p.end_date else None,
                "subscriptionsCount": subs_count or 0,
                "features": p.features_json or {},
                "flags": p.flags_json or {},
                "createdAt": p.created_at.isoformat() if p.created_at else "",
            }
            for p, subs_count in rows
        ],
        "meta": {"total": total, "page": (offset // limit) + 1, "limit": limit},
    }


@router.post("/plans", status_code=201)
async def create_plan(
    body: dict,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Create a new plan."""
    from decimal import Decimal
    from datetime import date as dt_date
    from app.models.plan import Plan
    from app.core.enums import BillingPeriod

    plan = Plan(
        tenant_id=user.tenant_id,
        name=body["name"],
        price=Decimal(str(body.get("price", 0))),
        billing_period=BillingPeriod(body.get("billingPeriod", "monthly")),
        min_qty=int(body.get("minQty", 1)),
        start_date=dt_date.fromisoformat(body["startDate"]) if body.get("startDate") else dt_date.today(),
        end_date=dt_date.fromisoformat(body["endDate"]) if body.get("endDate") else None,
        features_json=body.get("features", {}),
        flags_json=body.get("flags", {}),
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)

    return {
        "id": str(plan.id),
        "name": plan.name,
        "price": float(plan.price),
        "billingPeriod": plan.billing_period.value,
    }


@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: UUID,
    body: dict,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Update a plan."""
    from decimal import Decimal
    from datetime import date as dt_date
    from sqlalchemy import select
    from app.models.plan import Plan
    from app.core.enums import BillingPeriod
    from app.exceptions.base import NotFoundException

    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.tenant_id == user.tenant_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise NotFoundException("Plan not found.")

    if "name" in body:
        plan.name = body["name"]
    if "price" in body:
        plan.price = Decimal(str(body["price"]))
    if "billingPeriod" in body:
        plan.billing_period = BillingPeriod(body["billingPeriod"])
    if "minQty" in body:
        plan.min_qty = int(body["minQty"])
    if "startDate" in body:
        plan.start_date = dt_date.fromisoformat(body["startDate"])
    if "endDate" in body:
        plan.end_date = dt_date.fromisoformat(body["endDate"]) if body["endDate"] else None
    if "features" in body:
        plan.features_json = body["features"]
    if "flags" in body:
        plan.flags_json = body["flags"]

    await db.flush()
    await db.refresh(plan)

    return {
        "id": str(plan.id),
        "name": plan.name,
        "price": float(plan.price),
        "billingPeriod": plan.billing_period.value,
    }


@router.delete("/plans/{plan_id}", status_code=204, response_class=Response)
async def delete_plan(
    plan_id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> Response:
    """Delete a plan."""
    from sqlalchemy import select
    from app.models.plan import Plan
    from app.exceptions.base import NotFoundException

    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.tenant_id == user.tenant_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise NotFoundException("Plan not found.")

    await db.delete(plan)
    await db.flush()
    return Response(status_code=204)

# ═══════════════════════════════════════════════════════════════
# Subscriptions
# ═══════════════════════════════════════════════════════════════

@router.get("/subscriptions")
async def list_subscriptions(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
) -> dict:
    """List subscriptions."""
    from app.core.enums import SubscriptionStatus
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload
    from app.models.subscription import Subscription
    
    enum_status = SubscriptionStatus(status) if status else None
    
    base_q = select(Subscription).where(Subscription.tenant_id == user.tenant_id)
    if enum_status:
        base_q = base_q.where(Subscription.status == enum_status)
        
    total_q = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = total_q.scalar() or 0
    
    offset = (page - 1) * limit
    q = base_q.options(
        selectinload(Subscription.plan),
        selectinload(Subscription.customer)
    ).order_by(Subscription.created_at.desc()).offset(offset).limit(limit)
    
    res = await db.execute(q)
    items = res.scalars().all()
    
    # Needs to match frontend assumptions or general backend conventions
    return {
        "data": [{
            "id": str(s.id),
            "number": s.number,
            "status": s.status.value if s.status else "draft",
            "planName": s.plan.name if s.plan else "Unknown",
            "customerName": s.customer.name if s.customer else "Unknown",
            "startDate": s.start_date.isoformat() if s.start_date else None,
            "expiryDate": s.expiry_date.isoformat() if s.expiry_date else None,
            "billingPeriod": s.plan.billing_period.value if s.plan else "monthly",
            "mrr": float(s.plan.price) if s.plan else 0.0,
            "createdAt": s.created_at.isoformat() if s.created_at else "",
        } for s in items],
        "meta": {
            "total": total,
            "page": page,
            "limit": limit
        }
    }

@router.get("/subscriptions/options")
async def get_subscription_options(
    search: str = Query(""),
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Get subscription options for filtering/dropdowns."""
    from sqlalchemy import select
    from app.models.subscription import Subscription
    
    # Just returning a few for dropdowns
    q = select(Subscription).where(Subscription.tenant_id == user.tenant_id)
    if search:
        q = q.where(Subscription.number.ilike(f"%{search}%"))
        
    res = await db.execute(q.limit(10))
    subs = res.scalars().all()
    
    return {
        "data": [{"label": s.number, "value": str(s.id)} for s in subs]
    }

# ═══════════════════════════════════════════════════════════════
# Customers
# ═══════════════════════════════════════════════════════════════

@router.get("/customers")
async def list_customers(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> dict:
    """List customers."""
    from app.services.company.customer import CustomerService
    
    svc = CustomerService(db, user.tenant_id)
    items = await svc.list_all(offset=offset, limit=limit)
    total = await svc.count()
    
    return {
        "data": [{
            "id": str(c.id),
            "name": c.name,
            "email": c.email,
            "role": getattr(c.role, "value", str(c.role)),
            "created_at": c.created_at.isoformat() if c.created_at else "",
        } for c in items],
        "meta": {
            "total": total,
            "offset": offset,
            "limit": limit
        }
    }

# ═══════════════════════════════════════════════════════════════
# Discount CRUD
# ═══════════════════════════════════════════════════════════════

@router.get("/discounts", response_model=DiscountListResponse)
async def list_discounts(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> DiscountListResponse:
    from app.repositories.billing import DiscountRepository
    repo = DiscountRepository(db, user.tenant_id)
    items = await repo.find_all(offset=offset, limit=limit)
    total = await repo.count()
    return DiscountListResponse(
        data=[DiscountResponse(**(i.__dict__)) for i in items],
        meta={"total": total, "page": (offset // limit) + 1, "limit": limit}
    )

@router.post("/discounts", status_code=201)
async def create_discount(
    body: DiscountCreateRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> DiscountResponse:
    from app.repositories.billing import DiscountRepository
    repo = DiscountRepository(db, user.tenant_id)
    discount = await repo.create({**body.model_dump(), "tenant_id": user.tenant_id})
    return DiscountResponse(**(discount.__dict__))

@router.delete("/discounts/{id}")
async def delete_discount(
    id: UUID,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
):
    from app.repositories.billing import DiscountRepository
    repo = DiscountRepository(db, user.tenant_id)
    await repo.delete(id)
    return {"status": "success"}

# ═══════════════════════════════════════════════════════════════
# Tax CRUD
# ═══════════════════════════════════════════════════════════════

@router.get("/taxes", response_model=TaxListResponse)
async def list_taxes(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> TaxListResponse:
    from app.repositories.billing import TaxRepository
    repo = TaxRepository(db, user.tenant_id)
    items = await repo.find_all(offset=offset, limit=limit)
    total = await repo.count()
    return TaxListResponse(
        data=[TaxResponse(**(i.__dict__)) for i in items],
        meta={"total": total, "page": (offset // limit) + 1, "limit": limit}
    )

@router.post("/taxes", status_code=201)
async def create_tax(
    body: TaxCreateRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> TaxResponse:
    from app.repositories.billing import TaxRepository
    repo = TaxRepository(db, user.tenant_id)
    tax = await repo.create({**body.model_dump(), "tenant_id": user.tenant_id})
    return TaxResponse(**(tax.__dict__))

# ═══════════════════════════════════════════════════════════════
# Quotation Templates
# ═══════════════════════════════════════════════════════════════

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
) -> TemplateListResponse:
    from app.repositories.billing import QuotationTemplateRepository
    repo = QuotationTemplateRepository(db, user.tenant_id)
    items = await repo.find_all(offset=offset, limit=limit)
    total = await repo.count()
    return TemplateListResponse(
        data=[
            TemplateResponse(
                id=i.id,
                name=i.name,
                validity_days=i.validity_days,
                plan_id=i.plan_id,
                plan_name=i.plan.name if i.plan else "Unknown",
                created_at=i.created_at
            ) for i in items
        ],
        meta={"total": total, "page": (offset // limit) + 1, "limit": limit}
    )

@router.post("/templates", status_code=201)
async def create_template(
    body: TemplateCreateRequest,
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> TemplateResponse:
    from app.repositories.billing import QuotationTemplateRepository
    repo = QuotationTemplateRepository(db, user.tenant_id)
    item = await repo.create({**body.model_dump(), "tenant_id": user.tenant_id})
    return TemplateResponse(
        id=item.id,
        name=item.name,
        validity_days=item.validity_days,
        plan_id=item.plan_id,
        created_at=item.created_at
    )
