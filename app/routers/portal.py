"""
Portal router — portal_user only.

Endpoints:
  GET   /portal/me                              — current user profile (basic)
  GET   /portal/profile                         — full profile
  PATCH /portal/profile                         — update name
  PATCH /portal/profile/address                 — update billing address
  POST  /portal/profile/change-password         — change password
  GET   /portal/my-subscription                 — subscription dashboard
  GET   /portal/my-subscription/change-plan/preview — preview plan change
  POST  /portal/my-subscription/change-plan     — execute plan change
  POST  /portal/my-subscription/cancel          — cancel subscription
  GET   /portal/invoices                        — list own invoices
  GET   /portal/invoices/{id}                   — get own invoice
  GET   /portal/invoices/{id}/pdf               — download own invoice PDF
  POST  /portal/invoices/{id}/pay               — pay an invoice
  GET   /portal/payments                        — payment history
  GET   /portal/sessions                        — list active sessions
  DELETE /portal/sessions/{id}                  — revoke a session

Every endpoint ≤ 10 lines. All logic in services.
"""

from __future__ import annotations
from decimal import Decimal
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
from app.schemas.portal import (
    PasswordChangeRequest,
    PortalAddressUpdateRequest,
    PortalPaymentListResponse,
    PortalProfileResponse,
    PortalProfileUpdateRequest,
    SessionListResponse,
)
from app.schemas.subscription import (
    CancelRequest,
    ChangePlanPreviewResponse,
    ChangePlanRequest,
    PortalSubscriptionResponse,
)
from app.services.billing.invoice_service import InvoiceService
from app.services.billing.payment_service import PaymentService
from app.services.billing.paypal_service import PayPalPaymentService
from app.services.billing.pdf_generator import InvoicePDFGenerator
from app.services.portal import PortalService
from app.services.subscriptions.portal import PortalSubscriptionService
from app.schemas.paypal import (
    PayPalCheckoutRequest,
    PayPalCheckoutResponse,
    PayPalFailureRequest,
    PayPalFailureResponse,
    PayPalSuccessRequest,
    PayPalSuccessResponse,
)

router = APIRouter(
    prefix="/portal",
    tags=["portal"],
    dependencies=[Depends(require_portal_user)],
)


# ── Helpers ──────────────────────────────────────────────────────


def _invoice_to_portal_response(inv) -> dict:
    """Map Invoice model to strictly matching frontend PortalInvoice interface."""
    return {
        "id": str(inv.id),
        "number": inv.invoice_number or "",
        "date": inv.created_at.isoformat() if inv.created_at else inv.due_date.isoformat(),
        "dueDate": inv.due_date.isoformat() if inv.due_date else "",
        "amount": float(inv.total) if inv.total else 0.0,
        "status": inv.status.value if inv.status else "draft"
    }

def _invoice_to_response(inv) -> InvoiceResponse:
    """Map Invoice model to portal response schema."""
    from app.schemas.billing import InvoiceResponse, InvoiceLineResponse

    return InvoiceResponse(
        id=inv.id,
        number=inv.invoice_number,
        subscription_id=inv.subscription_id,
        customer_id=inv.customer_id,
        subscriptionName=inv.subscription.name if inv.subscription else "Unknown",
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
                taxPercent=0.0,
                discount=Decimal("0"),
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
        customerId=p.customer_id,
        method=p.method,
        amount=p.amount,
        paidAt=p.paid_at,
        createdAt=p.created_at,
    )


def serialize_sub(sub) -> dict:
    return {
        "id": str(sub.id),
        "name": sub.name,
        "status": sub.status,
        "planId": sub.plan_id,
        "customerId": sub.customer_id,
        "planName": sub.plan.name if sub.plan else "Unknown Plan",
        "startDate": sub.start_date,
        "nextBillingDate": sub.next_billing_date,
        "currentPeriodEnd": sub.current_period_end,
    }


# ═══════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════


@router.get("/me")
async def get_me(
    user: TokenPayload = Depends(require_portal_user),
) -> dict:
    """Return basic authenticated portal_user info."""
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
    }


@router.get("/profile")
async def get_profile(
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Return full portal_user profile."""
    svc = PortalService(db, user.user_id, user.tenant_id)
    prof = await svc.get_profile()
    return {"data": prof}


@router.patch("/profile")
async def update_profile(
    body: PortalProfileUpdateRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Update portal_user name."""
    svc = PortalService(db, user.user_id, user.tenant_id)
    prof = await svc.update_profile(body)
    return {"data": prof}


@router.patch("/profile/address")
async def update_address(
    body: PortalAddressUpdateRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Update billing address."""
    svc = PortalService(db, user.user_id, user.tenant_id)
    prof = await svc.update_address(body)
    return {"data": prof}


@router.post("/profile/change-password")
async def change_password(
    body: PasswordChangeRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Change password (verifies current password)."""
    svc = PortalService(db, user.user_id, user.tenant_id)
    return await svc.change_password(body)


# ═══════════════════════════════════════════════════════════════
# Subscription
# ═══════════════════════════════════════════════════════════════


@router.get("/my-subscription")
async def get_my_subscription(
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Get portal_user's active subscription with plan + lines + invoices."""
    from app.exceptions.base import NotFoundException
    svc = PortalSubscriptionService(db, user.tenant_id, user.user_id)
    try:
        sub = await svc.get_my_subscription()
        return {"data": sub}
    except NotFoundException:
        return {"data": None}


@router.post("/my-subscription/create")
async def create_subscription(
    body: ChangePlanRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Create a new subscription if user doesn't have one."""
    svc = PortalSubscriptionService(db, user.tenant_id, user.user_id)
    res = await svc.create_subscription(body.plan_id)
    return {"data": res}


@router.get("/my-subscription/change-plan/preview")
async def change_plan_preview(
    plan_id: UUID = Query(..., description="Target plan UUID"),
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Preview a plan change (upgrade/downgrade)."""
    svc = PortalSubscriptionService(db, user.tenant_id, user.user_id)
    preview = await svc.change_plan_preview(plan_id)
    return {"data": preview}


@router.post("/my-subscription/change-plan")
async def change_plan(
    body: ChangePlanRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Execute a plan change (upgrade immediately, downgrade scheduled)."""
    svc = PortalSubscriptionService(db, user.tenant_id, user.user_id)
    res = await svc.change_plan(body.plan_id)
    return {"data": res}


@router.post("/my-subscription/cancel")
async def cancel_subscription(
    body: CancelRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Cancel portal_user's subscription."""
    svc = PortalSubscriptionService(db, user.tenant_id, user.user_id)
    res = await svc.cancel(body.reason)
    return {"data": res}


# ═══════════════════════════════════════════════════════════════
# Invoice Endpoints
# ═══════════════════════════════════════════════════════════════


@router.get("/invoices")
async def list_invoices(
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
    status: str | None = Query(None, description="Filter by status"),
    dateFrom: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    dateTo: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    """List invoices for the authenticated customer."""
    svc = InvoiceService(db, user.tenant_id)
    items, total = await svc.list_invoices_for_customer(
        user.user_id, 
        status=status,
        date_from=dateFrom,
        date_to=dateTo,
        offset=offset, 
        limit=limit
    )
    return {
        "data": [_invoice_to_portal_response(i) for i in items],
        "meta": {"total": total, "offset": offset, "limit": limit}
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Get a single invoice for the authenticated customer."""
    svc = InvoiceService(db, user.tenant_id)
    inv = await svc.get_invoice_for_customer(invoice_id, user.user_id)
    return {"data": _invoice_to_response(inv)}


@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> Response:
    """Download invoice PDF (portal mode — no internal data)."""
    # Manually fetch with joinedload to avoid lazy loading issues in PDF generator
    from app.models.invoice import Invoice
    from app.models.invoice_line import InvoiceLine
    from app.models.tenant import Tenant
    from sqlalchemy.orm import joinedload
    from sqlalchemy import select

    result = await db.execute(
        select(Invoice)
        .options(
            joinedload(Invoice.lines)
            .joinedload(InvoiceLine.product)
        )
        .where(Invoice.id == invoice_id, Invoice.customer_id == user.user_id)
    )
    inv = result.unique().scalar_one_or_none()
    
    if not inv:
        from app.exceptions.base import NotFoundException
        raise NotFoundException("Invoice not found.")

    # Fetch tenant for name/branding
    tenant_res = await db.execute(
        select(Tenant.name).where(Tenant.id == user.tenant_id)
    )
    tenant_name = tenant_res.scalar() or "Company"

    pdf = InvoicePDFGenerator().generate(inv, mode="portal", tenant_name=tenant_name)
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
) -> dict:
    """Pay an invoice (full outstanding amount)."""
    svc = PaymentService(db, user.tenant_id)
    payment = await svc.portal_pay(
        invoice_id=invoice_id,
        customer_id=user.user_id,
        method=body.method,
    )
    return {"data": _payment_to_response(payment)}


# ═══════════════════════════════════════════════════════════════
# PayPal Payment Gateway
# ═══════════════════════════════════════════════════════════════


@router.post("/invoices/{invoice_id}/paypal/checkout")
async def paypal_checkout(
    invoice_id: UUID,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> PayPalCheckoutResponse:
    """Initiate PayPal checkout for an invoice — returns approval URL."""
    svc = PayPalPaymentService(db, user.tenant_id)
    result = await svc.create_checkout(
        invoice_id=invoice_id,
        customer_id=user.user_id,
    )
    return PayPalCheckoutResponse(**result)


@router.post("/invoices/{invoice_id}/paypal/success")
async def paypal_success(
    invoice_id: UUID,
    body: PayPalSuccessRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> PayPalSuccessResponse:
    """Handle PayPal payment success — captures payment and records it."""
    svc = PayPalPaymentService(db, user.tenant_id)
    result = await svc.handle_success(
        paypal_order_id=body.paypal_order_id,
        invoice_id=invoice_id,
        customer_id=user.user_id,
    )
    return PayPalSuccessResponse(**result)


@router.post("/invoices/{invoice_id}/paypal/failure")
async def paypal_failure(
    invoice_id: UUID,
    body: PayPalFailureRequest,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> PayPalFailureResponse:
    """Handle PayPal payment failure or cancellation."""
    svc = PayPalPaymentService(db, user.tenant_id)
    result = await svc.handle_failure(
        paypal_order_id=body.paypal_order_id,
        invoice_id=invoice_id,
        reason=body.reason or "Payment cancelled by user",
    )
    return PayPalFailureResponse(**result)


# ═══════════════════════════════════════════════════════════════
# Payment History
# ═══════════════════════════════════════════════════════════════


@router.get("/payments")
async def list_payments(
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict:
    """Payment history for the authenticated customer."""
    svc = PortalService(db, user.user_id, user.tenant_id)
    res = await svc.list_payments(offset=offset, limit=limit)
    return {
        "data": res.items,
        "meta": {"total": res.total, "has_overdue": res.has_overdue, "offset": offset, "limit": limit}
    }


# ═══════════════════════════════════════════════════════════════
# Session Management
# ═══════════════════════════════════════════════════════════════


@router.get("/sessions")
async def list_sessions(
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """List all active sessions."""
    svc = PortalService(db, user.user_id, user.tenant_id)
    res = await svc.list_sessions()
    return {
        "data": res.items,
        "meta": {"total": res.total}
    }


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: UUID,
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """Revoke a specific session."""
    svc = PortalService(db, user.user_id, user.tenant_id)
    res = await svc.revoke_session(session_id)
    return {"data": res}


@router.get("/plans")
async def get_plans(
    user: TokenPayload = Depends(require_portal_user),
    db: AsyncSession = Depends(get_tenant_session),
) -> dict:
    """List active plans for the tenant."""
    from sqlalchemy import select
    from app.models.plan import Plan
    result = await db.execute(
        select(Plan).where(
            Plan.tenant_id == user.tenant_id,
            Plan.deleted_at.is_(None)
        )
    )
    plans = result.scalars().all()
    return {
        "data": [{
            "id": str(p.id),
            "name": p.name,
            "description": p.features_json.get("description", "No description") if isinstance(p.features_json, dict) else "No description",
            "price": str(p.price),
            "billing_period": p.billing_period.value,
            "features": p.features_json.get("items", []) if isinstance(p.features_json, dict) else [],
        } for p in plans]
    }
