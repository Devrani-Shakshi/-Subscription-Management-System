import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/submanager"

async def fix_db():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE discounts ALTER COLUMN end_date DROP NOT NULL;"))
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_db())
