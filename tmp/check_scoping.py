import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/submanager"

async def check_tenants_and_templates():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name FROM tenants;"))
        tenants = res.fetchall()
        print(f"Tenants: {tenants}")
        
        res = await conn.execute(text("SELECT id, name, tenant_id FROM quotation_templates;"))
        templates = res.fetchall()
        print(f"Templates: {templates}")

        res = await conn.execute(text("SELECT email, tenant_id FROM users;"))
        users = res.fetchall()
        print(f"Users: {users}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_tenants_and_templates())
