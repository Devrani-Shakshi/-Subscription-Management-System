import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/submanager"

async def check_data():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, tenant_id FROM quotation_templates;"))
        rows = res.fetchall()
        print(f"Templates: {rows}")
        
        res = await conn.execute(text("SELECT id, name, tenant_id FROM discounts;"))
        rows = res.fetchall()
        print(f"Discounts: {rows}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_data())
