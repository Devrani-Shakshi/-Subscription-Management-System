import asyncio
import uuid
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import text, select
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
        
        # Get primary tenant created by seed_full.py
        result = await session.execute(select(Tenant).where(Tenant.name == 'Nova Systems'))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            result = await session.execute(select(Tenant).limit(1))
            tenant = result.scalar_one_or_none()
            
        if not tenant:
            print("No tenant found!")
            return
            
        tid = tenant.id
        print(f"Seeding 100 records into Tenant: {tenant.name} ({tid})")

        # Create one admin if not exists
        result = await session.execute(select(User).where(User.tenant_id == tid).where(User.role == UserRole.COMPANY))
        company_admin = result.scalars().first()
        if not company_admin:
            company_admin = User(id=uuid.uuid4(), email=f'admin_nova_100@novasys.ai', password_hash=pw, role=UserRole.COMPANY, tenant_id=tid, name='Nova Admin')
            session.add(company_admin)
            await session.flush()
            
        # Mock Session
        sess = Session(id=uuid.uuid4(), user_id=company_admin.id, tenant_id=tid, refresh_token_hash="abc", family_id=uuid.uuid4(), device_fingerprint="browser", ip_subnet="127.0.0.1", expires_at=datetime.now(timezone.utc) + timedelta(days=7))
        session.add(sess)

        # Tax & Discount
        tax = Tax(id=uuid.uuid4(), tenant_id=tid, name="Standard VAT", rate=Decimal("20.0"), type="percentage")
        session.add(tax)

        disc = Discount(id=uuid.uuid4(), tenant_id=tid, name="Spring Promo", type=DiscountType.PERCENT, value=Decimal("10"), min_purchase=Decimal("0"), min_qty=1, start_date=date.today(), end_date=date.today()+timedelta(days=365), usage_limit=1000, used_count=0, applies_to=DiscountAppliesTo.SUBSCRIPTION)
        session.add(disc)
        await session.flush()

        prods = []
        plans = []
        users = []
        
        # 100 Products, Plans, Users
        for i in range(100):
            p = Product(id=uuid.uuid4(), tenant_id=tid, name=f'Enterprise Product {i}', type='service', sales_price=Decimal(f"{10.0 + i}"), cost_price=Decimal("5.0"))
            session.add(p)
            prods.append(p)
            
            pv = ProductVariant(id=uuid.uuid4(), tenant_id=tid, product_id=p.id, attribute="Tier", value=f"Tier {i%3}", extra_price=Decimal("5.0"))
            session.add(pv)

            pl = Plan(id=uuid.uuid4(), tenant_id=tid, name=f'Premium Plan {i}', price=Decimal(f"{50.0 + i}"), billing_period=BillingPeriod.MONTHLY, start_date=date.today())
            session.add(pl)
            plans.append(pl)
            
            qt = QuotationTemplate(id=uuid.uuid4(), tenant_id=tid, name=f"Standard Quote {i}", validity_days=30, plan_id=pl.id)
            session.add(qt)

            u = User(id=uuid.uuid4(), email=f'customer_{uuid.uuid4().hex[:6]}@domain.com', password_hash=pw, role=UserRole.PORTAL_USER, tenant_id=tid, name=f'Customer {i}')
            session.add(u)
            users.append(u)

        await session.flush()

        # 100 Subscriptions, Invoices, Payments, etc.
        for i in range(100):
            u = users[i]
            pl = plans[i]
            p = prods[i]

            s = Subscription(id=uuid.uuid4(), tenant_id=tid, number=f'SUB-{uuid.uuid4().hex[:6]}-{i}', customer_id=u.id, plan_id=pl.id, start_date=date.today() - timedelta(days=i), expiry_date=date.today()+timedelta(days=30), status=random.choice(list(SubscriptionStatus)))
            session.add(s)
            
            churn = ChurnScore(id=uuid.uuid4(), tenant_id=tid, customer_id=u.id, score=random.randint(1, 99), signals_json={}, computed_at=datetime.now(timezone.utc))
            session.add(churn)

            sl = SubscriptionLine(id=uuid.uuid4(), tenant_id=tid, subscription_id=s.id, product_id=p.id, qty=1, unit_price=p.sales_price, tax_ids=[tax.id])
            session.add(sl)

            inv_status = random.choice(list(InvoiceStatus))
            inv = Invoice(id=uuid.uuid4(), tenant_id=tid, invoice_number=f'INV-{uuid.uuid4().hex[:6]}-{i}', subscription_id=s.id, customer_id=u.id, status=inv_status, due_date=date.today(), subtotal=pl.price, total=pl.price, amount_paid=pl.price if inv_status == InvoiceStatus.PAID else Decimal("0"))
            session.add(inv)
            
            if inv_status == InvoiceStatus.PAID:
                pay = Payment(id=uuid.uuid4(), tenant_id=tid, invoice_id=inv.id, customer_id=u.id, method=random.choice(list(PaymentMethod)), amount=pl.price, paid_at=datetime.now(timezone.utc))
                session.add(pay)
            elif inv_status == InvoiceStatus.OVERDUE:
                dun = DunningSchedule(id=uuid.uuid4(), tenant_id=tid, invoice_id=inv.id, attempt_number=1, action=DunningAction.RETRY, channel="email", scheduled_at=datetime.now(timezone.utc), status=DunningStatus.PENDING)
                session.add(dun)

            il = InvoiceLine(id=uuid.uuid4(), tenant_id=tid, invoice_id=inv.id, product_id=p.id, qty=1, unit_price=p.sales_price, tax_id=tax.id, discount_id=disc.id)
            session.add(il)

            rev = RevenueRecognition(id=uuid.uuid4(), tenant_id=tid, invoice_id=inv.id, recognized_amount=pl.price, recognition_date=date.today(), period="2026-04")
            session.add(rev)

            audit = AuditLog(id=uuid.uuid4(), tenant_id=tid, actor_id=company_admin.id, actor_role=UserRole.COMPANY, entity_type="subscription", entity_id=s.id, action=AuditAction.CREATE, session_id=sess.id)
            session.add(audit)

    await session.commit()
    print(f'Done generating 100 sets for tenant {tenant.name}!')

asyncio.run(main())
