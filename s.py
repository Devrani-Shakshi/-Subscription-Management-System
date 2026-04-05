import asyncio
import uuid
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

from app.core.enums import *
from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.subscription_line import SubscriptionLine
from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.payment import Payment
from app.models.discount import Discount
from app.models.tax import Tax
from app.models.audit_log import AuditLog
from app.models.dunning_schedule import DunningSchedule
from app.models.churn_score import ChurnScore
from app.models.revenue_recognition import RevenueRecognition
from app.models.quotation_template import QuotationTemplate
from app.models.session import Session

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    session = sessionmaker(engine, class_=AsyncSession)()
    pw = "$2b$12$s4KEiWrdmG1ymG2kWH0Z7.NzUX1WAPOzjyV8q8.YG8BcRyDbxaeT2"

    async with session.begin():
        await session.execute(text("SET LOCAL app.tenant_id = 'SUPER'"))
        
        for i in range(100):
            tid = uuid.uuid4()
            t = Tenant(id=tid, name=f'Company {i}', slug=f'c{tid.hex[:8]}', status=TenantStatus.ACTIVE)
            session.add(t)
            await session.flush()

            u = User(id=uuid.uuid4(), email=f'u{tid.hex[:8]}@a.com', password_hash=pw, role=UserRole.COMPANY, tenant_id=tid, name='User A')
            session.add(u)
            await session.flush()

            sess = Session(id=uuid.uuid4(), user_id=u.id, tenant_id=tid, refresh_token_hash="abc", family_id=uuid.uuid4(), device_fingerprint="browser", ip_subnet="127.0.0.1", expires_at=datetime.now(timezone.utc) + timedelta(days=7))
            session.add(sess)

            tax = Tax(id=uuid.uuid4(), tenant_id=tid, name="VAT", rate=Decimal("20.0"), type="percentage")
            session.add(tax)

            disc = Discount(id=uuid.uuid4(), tenant_id=tid, name="Promo", type=DiscountType.PERCENT, value=Decimal("10"), min_purchase=Decimal("0"), min_qty=1, start_date=date.today(), end_date=date.today()+timedelta(days=365), usage_limit=100, used_count=0, applies_to=DiscountAppliesTo.SUBSCRIPTION)
            session.add(disc)

            p = Product(id=uuid.uuid4(), tenant_id=tid, name='Prod', type='service', sales_price=Decimal("10.0"), cost_price=Decimal("5.0"))
            session.add(p)
            await session.flush()

            pv = ProductVariant(id=uuid.uuid4(), tenant_id=tid, product_id=p.id, attribute="Tier", value="Gold", extra_price=Decimal("5.0"))
            session.add(pv)

            pl = Plan(id=uuid.uuid4(), tenant_id=tid, name='Plan', price=Decimal("10.0"), billing_period=BillingPeriod.MONTHLY, start_date=date.today())
            session.add(pl)
            await session.flush()

            qt = QuotationTemplate(id=uuid.uuid4(), tenant_id=tid, name="Default", validity_days=30, plan_id=pl.id)
            session.add(qt)

            s = Subscription(id=uuid.uuid4(), tenant_id=tid, number=f'SUB{i}', customer_id=u.id, plan_id=pl.id, start_date=date.today(), expiry_date=date.today()+timedelta(days=30), status=SubscriptionStatus.ACTIVE)
            session.add(s)
            await session.flush()

            sl = SubscriptionLine(id=uuid.uuid4(), tenant_id=tid, subscription_id=s.id, product_id=p.id, qty=1, unit_price=Decimal("10.0"), tax_ids=[tax.id])
            session.add(sl)

            inv = Invoice(id=uuid.uuid4(), tenant_id=tid, invoice_number=f'INV{i}', subscription_id=s.id, customer_id=u.id, status=InvoiceStatus.PAID, due_date=date.today(), subtotal=Decimal("10"), total=Decimal("10"), amount_paid=Decimal("10"))
            session.add(inv)
            await session.flush()

            il = InvoiceLine(id=uuid.uuid4(), tenant_id=tid, invoice_id=inv.id, product_id=p.id, qty=1, unit_price=Decimal("10.0"), tax_id=tax.id, discount_id=disc.id)
            session.add(il)

            pay = Payment(id=uuid.uuid4(), tenant_id=tid, invoice_id=inv.id, customer_id=u.id, method=PaymentMethod.CARD, amount=Decimal("10"), paid_at=datetime.now(timezone.utc))
            session.add(pay)

            dun = DunningSchedule(id=uuid.uuid4(), tenant_id=tid, invoice_id=inv.id, attempt_number=1, action=DunningAction.RETRY, channel="email", scheduled_at=datetime.now(timezone.utc), status=DunningStatus.PENDING)
            session.add(dun)

            churn = ChurnScore(id=uuid.uuid4(), tenant_id=tid, customer_id=u.id, score=10, signals_json={}, computed_at=datetime.now(timezone.utc))
            session.add(churn)

            rev = RevenueRecognition(id=uuid.uuid4(), tenant_id=tid, invoice_id=inv.id, recognized_amount=Decimal("10"), recognition_date=date.today(), period="2026-04")
            session.add(rev)

            audit = AuditLog(id=uuid.uuid4(), tenant_id=tid, actor_id=u.id, actor_role=UserRole.COMPANY, entity_type="subscription", entity_id=s.id, action=AuditAction.CREATE, session_id=sess.id)
            session.add(audit)

    await session.commit()
    print('Done generating 100 sets!')

asyncio.run(main())
