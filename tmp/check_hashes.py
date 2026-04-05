import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

async def check_hashes():
    url = os.getenv("DATABASE_URL")
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT email, password_hash FROM users WHERE email='demo@demodata.com'"))
            user = result.fetchone()
            if user:
                print(f"Email: {user[0]}")
                print(f"Hash: {user[1]}")
            else:
                print("User not found")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_hashes())
