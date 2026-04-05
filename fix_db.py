import asyncio
from sqlalchemy import text
from app.core.database import async_session_factory

async def fix_enum():
    async with async_session_factory() as db:
        try:
            # Cannot run ALTER TYPE inside a transaction block easily, but autocommit can work:
            await db.execute(text("ALTER TYPE invoice_status ADD VALUE 'overdue';"))
            await db.commit()
            print("Added overdue")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(fix_enum())
