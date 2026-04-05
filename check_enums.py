import asyncio
from app.core.database import async_session_factory
from sqlalchemy import text

async def main():
    async with async_session_factory() as s:
        res1 = await s.execute(text("SELECT enum_range(NULL::dunning_status)"))
        print("dunning_status:", res1.scalar())
        res2 = await s.execute(text("SELECT enum_range(NULL::dunning_action)"))
        print("dunning_action:", res2.scalar())

if __name__ == "__main__":
    asyncio.run(main())
