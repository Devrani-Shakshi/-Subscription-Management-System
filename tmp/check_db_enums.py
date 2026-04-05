import asyncio
from app.core.database import async_session_factory
from sqlalchemy import text

async def check_enums():
    async with async_session_factory() as s:
        try:
            res = await s.execute(text("SELECT enum_range(NULL::invoice_status)"))
            print("invoice_status:", res.scalar())
        except Exception as e:
            print(f"Error checking invoice_status: {e}")
            
        try:
            res = await s.execute(text("SELECT enum_range(NULL::subscription_status)"))
            print("subscription_status:", res.scalar())
        except Exception as e:
            print(f"Error checking subscription_status: {e}")

if __name__ == "__main__":
    asyncio.run(check_enums())
