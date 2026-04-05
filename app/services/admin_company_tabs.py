"""
Isolated service for admin company tabs (Subs, Customers, Invoices)
"""
from typing import Any
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subscription import Subscription
from app.models.user import User
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.churn_score import ChurnScore


class AdminCompanyTabsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_subscriptions(self, tenant_id: uuid.UUID, page: int, limit: int) -> dict[str, Any]:
        offset = (page - 1) * limit
        
        # Total count
        count_stmt = select(func.count(Subscription.id)).where(Subscription.tenant_id == tenant_id)
        total = await self.db.scalar(count_stmt) or 0
        
        # Fetch items
        stmt = (
            select(Subscription, User, Plan)
            .join(User, Subscription.customer_id == User.id)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        data = []
        for sub, user, plan in rows:
            data.append({
                "id": str(sub.id),
                "customerName": user.name,
                "planName": plan.name,
                "status": sub.status.value,
                "mrr": float(plan.price),  # simplistic MRR
                "startDate": sub.start_date.isoformat(),
                "endDate": sub.expiry_date.isoformat() if sub.expiry_date else None,
            })
            
        return {
            "data": data,
            "meta": {"total": total, "page": page, "limit": limit}
        }

    async def get_customers(self, tenant_id: uuid.UUID, page: int, limit: int) -> dict[str, Any]:
        offset = (page - 1) * limit
        
        # Fetch only portal_user role
        from app.core.enums import UserRole
        base_cond = (User.tenant_id == tenant_id) & (User.role == UserRole.PORTAL_USER)
        
        count_stmt = select(func.count(User.id)).where(base_cond)
        total = await self.db.scalar(count_stmt) or 0
        
        # Subquery or outerjoin for active subscription and churn score
        # For simplicity, we fetch users, then execute queries for their subs, or use joinedload (but one-to-many isn't perfectly scalar here)
        # Doing simple active sub lookup per user
        user_stmt = select(User).where(base_cond).order_by(User.created_at.desc()).offset(offset).limit(limit)
        user_res = await self.db.scalars(user_stmt)
        users = user_res.all()
        
        data = []
        for u in users:
            # fetch sub
            sub_stmt = select(Subscription, Plan).join(Plan).where(Subscription.customer_id == u.id).order_by(Subscription.created_at.desc()).limit(1)
            sub_res = await self.db.execute(sub_stmt)
            sub_row = sub_res.first()
            
            sub_status = "none"
            plan_name = "None"
            if sub_row:
                sub_status = sub_row[0].status.value
                plan_name = sub_row[1].name
                
            data.append({
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "subscriptionStatus": sub_status,
                "planName": plan_name,
                "churnScore": 0, # Placeholder
            })
            
        return {
            "data": data,
            "meta": {"total": total, "page": page, "limit": limit}
        }

    async def get_invoices(self, tenant_id: uuid.UUID, page: int, limit: int) -> dict[str, Any]:
        offset = (page - 1) * limit
        
        count_stmt = select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
        total = await self.db.scalar(count_stmt) or 0
        
        stmt = select(Invoice).where(Invoice.tenant_id == tenant_id).order_by(Invoice.created_at.desc()).offset(offset).limit(limit)
        res = await self.db.scalars(stmt)
        invoices = res.all()
        
        data = []
        for i in invoices:
            data.append({
                "id": str(i.id),
                "number": i.invoice_number,
                "status": i.status.value,
                "total": float(i.total),
                "dueDate": i.due_date.isoformat(),
            })
            
        return {
            "data": data,
            "meta": {"total": total, "page": page, "limit": limit}
        }
