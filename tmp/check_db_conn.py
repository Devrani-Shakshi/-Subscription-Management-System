import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv()

async def check_db():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL not found in .env")
        return
    print(f"Connecting to {url}...")
    try:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            print("Successfully connected to the database.")
        await engine.dispose()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
