import asyncio
import uuid
from app.core.database import async_session_factory
from app.routers.company import list_payments, get_payment_summary
from app.schemas.auth import TokenPayload

async def test_payments():
    # We need a tenant_id and a user_id. Let's find them.
    async with async_session_factory() as s:
        from sqlalchemy import text
        res = await s.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant_id = res.scalar()
        if not tenant_id:
            print("No tenants found!")
            return
        
        res = await s.execute(text(f"SELECT id FROM users WHERE tenant_id = '{tenant_id}' LIMIT 1"))
        user_id = res.scalar()
        if not user_id:
            # Try any user
            res = await s.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = res.scalar()
            if not user_id:
                user_id = uuid.uuid4()
        
        print(f"Testing with tenant_id: {tenant_id}, user_id: {user_id}")
        
        user = TokenPayload(
            user_id=user_id,
            role="company",
            tenant_id=tenant_id,
            email="demo@example.com"
        )
        
        try:
            print("Calling get_payment_summary...")
            summary = await get_payment_summary(user=user, db=s)
            print("Summary:", summary)
        except Exception as e:
            import traceback
            print(f"Error in get_payment_summary: {e}")
            traceback.print_exc()

        try:
            print("\nCalling list_payments...")
            payments = await list_payments(user=user, db=s, offset=0, limit=50)
            print("Payments count:", len(payments.data))
        except Exception as e:
            import traceback
            print(f"Error in list_payments: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_payments())
