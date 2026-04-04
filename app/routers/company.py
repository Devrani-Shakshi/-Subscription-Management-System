"""
Company router — company role only.

All routes guarded by Depends(require_company).
tenant_id always read from request.state.tenant (via JWT middleware).
Every endpoint ≤ 10 lines. All logic in services.

Routes:
  Products:      GET/POST /products · GET/PATCH/DELETE /products/{id}
                 GET/POST /products/{id}/variants
                 DELETE   /products/{id}/variants/{variant_id}
  Plans:         GET/POST /plans · GET/PATCH/DELETE /plans/{id}
                 GET      /plans/{id}/preview
  Customers:     GET /customers · GET /customers/{id}
                 POST /customers/invite
  Templates:     GET/POST /templates · GET/PATCH/DELETE /templates/{id}
  Discounts:     GET/POST /discounts · GET/PATCH/DELETE /discounts/{id}
  Taxes:         GET/POST /taxes · GET/PATCH/DELETE /taxes/{id}
  Subscriptions: GET/POST /subscriptions · GET/PATCH /subscriptions/{id}
                 POST /subscriptions/{id}/activate
                 POST /subscriptions/{id}/close
                 POST /subscriptions/{id}/upgrade
                 POST /subscriptions/{id}/downgrade
                 POST /subscriptions/bulk
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SubscriptionStatus
from app.dependencies.guards import get_tenant_session, require_company
from app.schemas.auth import TokenPayload
from app.schemas.company import (
    CustomerInviteSchema,
    DiscountCreate,
    DiscountUpdate,
    PlanCreate,
    PlanUpdate,
    ProductCreate,
    ProductUpdate,
    TaxCreate,
    TaxUpdate,
    TemplateCreate,
    TemplateUpdate,
    VariantCreate,
)
from app.schemas.subscription import (
    BulkSubscriptionCreate,
    DowngradeRequest,
    SubscriptionCreate,
    SubscriptionUpdate,
    UpgradeRequest,
)
from app.services.company import (
    CustomerService,
    DiscountService,
    PlanService,
    ProductService,
    TaxService,
    TemplateService,
)
from app.services.subscriptions import (
    DowngradeService,
    SubscriptionService,
    UpgradeService,
)

router = APIRouter(
    prefix="/company",
    tags=["company"],
    dependencies=[Depends(require_company)],
)


# ═══════════════════════════════════════════════════════════════
# Helper to construct services from DI
# ═══════════════════════════════════════════════════════════════

def _product_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> ProductService:
    return ProductService(db, user.tenant_id)


def _plan_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> PlanService:
    return PlanService(db, user.tenant_id)


def _customer_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> CustomerService:
    return CustomerService(db, user.tenant_id)


def _template_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> TemplateService:
    return TemplateService(db, user.tenant_id)


def _discount_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> DiscountService:
    return DiscountService(db, user.tenant_id)


def _tax_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> TaxService:
    return TaxService(db, user.tenant_id)


# ═══════════════════════════════════════════════════════════════
# Products
# ═══════════════════════════════════════════════════════════════

@router.get("/products")
async def list_products(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    svc: ProductService = Depends(_product_svc),
) -> list[dict]:
    items = await svc.list_all(offset=offset, limit=limit)
    return [_product_to_dict(p) for p in items]


@router.post("/products", status_code=201)
async def create_product(
    body: ProductCreate,
    svc: ProductService = Depends(_product_svc),
) -> dict:
    product = await svc.create(body)
    return product.to_dict()


@router.get("/products/{product_id}")
async def get_product(
    product_id: UUID,
    svc: ProductService = Depends(_product_svc),
) -> dict:
    product = await svc.get_by_id(product_id)
    return _product_to_dict(product)


@router.patch("/products/{product_id}")
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    svc: ProductService = Depends(_product_svc),
) -> dict:
    product = await svc.update(product_id, body)
    return product.to_dict()


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    svc: ProductService = Depends(_product_svc),
) -> None:
    await svc.delete(product_id)


# ── Product Variants ─────────────────────────────────────────────

@router.get("/products/{product_id}/variants")
async def list_variants(
    product_id: UUID,
    svc: ProductService = Depends(_product_svc),
) -> list[dict]:
    variants = await svc.list_variants(product_id)
    return [v.to_dict() for v in variants]


@router.post("/products/{product_id}/variants", status_code=201)
async def create_variant(
    product_id: UUID,
    body: VariantCreate,
    svc: ProductService = Depends(_product_svc),
) -> dict:
    variant = await svc.create_variant(product_id, body)
    return variant.to_dict()


@router.delete(
    "/products/{product_id}/variants/{variant_id}", status_code=204,
)
async def delete_variant(
    product_id: UUID,
    variant_id: UUID,
    svc: ProductService = Depends(_product_svc),
) -> None:
    await svc.delete_variant(product_id, variant_id)


# ═══════════════════════════════════════════════════════════════
# Plans
# ═══════════════════════════════════════════════════════════════

@router.get("/plans")
async def list_plans(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    svc: PlanService = Depends(_plan_svc),
) -> list[dict]:
    plans = await svc.list_all(offset=offset, limit=limit)
    return [p.to_dict() for p in plans]


@router.post("/plans", status_code=201)
async def create_plan(
    body: PlanCreate,
    svc: PlanService = Depends(_plan_svc),
) -> dict:
    plan = await svc.create(body)
    return plan.to_dict()


@router.get("/plans/{plan_id}")
async def get_plan(
    plan_id: UUID,
    svc: PlanService = Depends(_plan_svc),
) -> dict:
    plan = await svc.get_by_id(plan_id)
    return plan.to_dict()


@router.patch("/plans/{plan_id}")
async def update_plan(
    plan_id: UUID,
    body: PlanUpdate,
    svc: PlanService = Depends(_plan_svc),
) -> dict:
    plan = await svc.update(plan_id, body)
    return plan.to_dict()


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: UUID,
    svc: PlanService = Depends(_plan_svc),
) -> None:
    await svc.delete(plan_id)


@router.get("/plans/{plan_id}/preview")
async def preview_plan(
    plan_id: UUID,
    svc: PlanService = Depends(_plan_svc),
) -> dict:
    preview = await svc.get_preview(plan_id)
    return preview.model_dump()


# ═══════════════════════════════════════════════════════════════
# Customers
# ═══════════════════════════════════════════════════════════════

@router.get("/customers")
async def list_customers(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    svc: CustomerService = Depends(_customer_svc),
) -> list[dict]:
    customers = await svc.list_all(offset=offset, limit=limit)
    return [c.to_dict() for c in customers]


@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: UUID,
    svc: CustomerService = Depends(_customer_svc),
) -> dict:
    customer = await svc.get_by_id(customer_id)
    return customer.to_dict()


@router.post("/customers/invite", status_code=201)
async def invite_customer(
    body: CustomerInviteSchema,
    svc: CustomerService = Depends(_customer_svc),
) -> dict:
    return await svc.invite(body)


# ═══════════════════════════════════════════════════════════════
# Templates
# ═══════════════════════════════════════════════════════════════

@router.get("/templates")
async def list_templates(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    svc: TemplateService = Depends(_template_svc),
) -> list[dict]:
    templates = await svc.list_all(offset=offset, limit=limit)
    return [t.to_dict() for t in templates]


@router.post("/templates", status_code=201)
async def create_template(
    body: TemplateCreate,
    svc: TemplateService = Depends(_template_svc),
) -> dict:
    template = await svc.create(body)
    return template.to_dict()


@router.get("/templates/{template_id}")
async def get_template(
    template_id: UUID,
    svc: TemplateService = Depends(_template_svc),
) -> dict:
    template = await svc.get_by_id(template_id)
    return template.to_dict()


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: UUID,
    body: TemplateUpdate,
    svc: TemplateService = Depends(_template_svc),
) -> dict:
    template = await svc.update(template_id, body)
    return template.to_dict()


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    svc: TemplateService = Depends(_template_svc),
) -> None:
    await svc.delete(template_id)


# ═══════════════════════════════════════════════════════════════
# Discounts
# ═══════════════════════════════════════════════════════════════

@router.get("/discounts")
async def list_discounts(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    svc: DiscountService = Depends(_discount_svc),
) -> list[dict]:
    discounts = await svc.list_all(offset=offset, limit=limit)
    return [d.to_dict() for d in discounts]


@router.post("/discounts", status_code=201)
async def create_discount(
    body: DiscountCreate,
    svc: DiscountService = Depends(_discount_svc),
) -> dict:
    discount = await svc.create(body)
    return discount.to_dict()


@router.get("/discounts/{discount_id}")
async def get_discount(
    discount_id: UUID,
    svc: DiscountService = Depends(_discount_svc),
) -> dict:
    discount = await svc.get_by_id(discount_id)
    return discount.to_dict()


@router.patch("/discounts/{discount_id}")
async def update_discount(
    discount_id: UUID,
    body: DiscountUpdate,
    svc: DiscountService = Depends(_discount_svc),
) -> dict:
    discount = await svc.update(discount_id, body)
    return discount.to_dict()


@router.delete("/discounts/{discount_id}", status_code=204)
async def delete_discount(
    discount_id: UUID,
    svc: DiscountService = Depends(_discount_svc),
) -> None:
    await svc.delete(discount_id)


# ═══════════════════════════════════════════════════════════════
# Taxes
# ═══════════════════════════════════════════════════════════════

@router.get("/taxes")
async def list_taxes(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    svc: TaxService = Depends(_tax_svc),
) -> list[dict]:
    taxes = await svc.list_all(offset=offset, limit=limit)
    return [t.to_dict() for t in taxes]


@router.post("/taxes", status_code=201)
async def create_tax(
    body: TaxCreate,
    svc: TaxService = Depends(_tax_svc),
) -> dict:
    tax = await svc.create(body)
    return tax.to_dict()


@router.get("/taxes/{tax_id}")
async def get_tax(
    tax_id: UUID,
    svc: TaxService = Depends(_tax_svc),
) -> dict:
    tax = await svc.get_by_id(tax_id)
    return tax.to_dict()


@router.patch("/taxes/{tax_id}")
async def update_tax(
    tax_id: UUID,
    body: TaxUpdate,
    svc: TaxService = Depends(_tax_svc),
) -> dict:
    tax = await svc.update(tax_id, body)
    return tax.to_dict()


@router.delete("/taxes/{tax_id}", status_code=204)
async def delete_tax(
    tax_id: UUID,
    svc: TaxService = Depends(_tax_svc),
) -> None:
    await svc.delete(tax_id)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _product_to_dict(product) -> dict:
    """Serialize product with variant count."""
    d = product.to_dict()
    variants = getattr(product, "variants", None)
    d["variants_count"] = len(variants) if variants else 0
    return d


# ═══════════════════════════════════════════════════════════════
# Subscription service factory
# ═══════════════════════════════════════════════════════════════

def _sub_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> SubscriptionService:
    return SubscriptionService(db, user.tenant_id)


def _upgrade_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> UpgradeService:
    return UpgradeService(db, user.tenant_id)


def _downgrade_svc(
    user: TokenPayload = Depends(require_company),
    db: AsyncSession = Depends(get_tenant_session),
) -> DowngradeService:
    return DowngradeService(db, user.tenant_id)


# ═══════════════════════════════════════════════════════════════
# Subscriptions
# ═══════════════════════════════════════════════════════════════

@router.get("/subscriptions")
async def list_subscriptions(
    status: Optional[SubscriptionStatus] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    svc: SubscriptionService = Depends(_sub_svc),
) -> list[dict]:
    items = await svc.list_all(status=status, offset=offset, limit=limit)
    return [s.to_dict() for s in items]


@router.post("/subscriptions", status_code=201)
async def create_subscription(
    body: SubscriptionCreate,
    svc: SubscriptionService = Depends(_sub_svc),
) -> dict:
    sub = await svc.create(
        customer_id=body.customer_id,
        plan_id=body.plan_id,
        start_date=body.start_date,
        expiry_date=body.expiry_date,
        payment_terms=body.payment_terms,
        lines=[ln.model_dump() for ln in body.lines],
    )
    return sub.to_dict()


@router.get("/subscriptions/{sub_id}")
async def get_subscription(
    sub_id: UUID,
    svc: SubscriptionService = Depends(_sub_svc),
) -> dict:
    sub = await svc.get_by_id(sub_id)
    return sub.to_dict()


@router.patch("/subscriptions/{sub_id}")
async def update_subscription(
    sub_id: UUID,
    body: SubscriptionUpdate,
    svc: SubscriptionService = Depends(_sub_svc),
) -> dict:
    sub = await svc.update(sub_id, body.model_dump(exclude_unset=True))
    return sub.to_dict()


@router.post("/subscriptions/{sub_id}/activate")
async def activate_subscription(
    sub_id: UUID,
    svc: SubscriptionService = Depends(_sub_svc),
) -> dict:
    sub = await svc.activate(sub_id)
    return sub.to_dict()


@router.post("/subscriptions/{sub_id}/close")
async def close_subscription(
    sub_id: UUID,
    svc: SubscriptionService = Depends(_sub_svc),
) -> dict:
    sub = await svc.close(sub_id)
    return sub.to_dict()


@router.post("/subscriptions/{sub_id}/upgrade")
async def upgrade_subscription(
    sub_id: UUID,
    body: UpgradeRequest,
    svc: UpgradeService = Depends(_upgrade_svc),
) -> dict:
    return await svc.execute(sub_id, body.new_plan_id)


@router.post("/subscriptions/{sub_id}/downgrade")
async def downgrade_subscription(
    sub_id: UUID,
    body: DowngradeRequest,
    svc: DowngradeService = Depends(_downgrade_svc),
) -> dict:
    return await svc.execute(sub_id, body.new_plan_id)


@router.post("/subscriptions/bulk", status_code=201)
async def bulk_create_subscriptions(
    body: BulkSubscriptionCreate,
    svc: SubscriptionService = Depends(_sub_svc),
) -> list[dict]:
    items_raw = [
        {
            "customer_id": it.customer_id,
            "plan_id": it.plan_id,
            "start_date": it.start_date,
            "expiry_date": it.expiry_date,
            "payment_terms": it.payment_terms,
            "lines": [ln.model_dump() for ln in it.lines],
        }
        for it in body.items
    ]
    subs = await svc.bulk_create(items_raw)
    return [s.to_dict() for s in subs]

