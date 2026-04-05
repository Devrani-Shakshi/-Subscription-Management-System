import asyncio
from app.core.database import async_session_factory
from sqlalchemy import text

async def main():
    async with async_session_factory() as s:
        res = await s.execute(text("SELECT id, name, slug, status FROM tenants"))
        tenants = res.all()
        print("Tenants in DB:")
        for t in tenants:
            print(f"- {t.name} (slug: {t.slug}, status: {t.status})")

if __name__ == "__main__":
    asyncio.run(main())
