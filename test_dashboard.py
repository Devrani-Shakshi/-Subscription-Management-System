import asyncio
import traceback
from app.core.database import async_session_factory
from app.routers.company import get_company_dashboard
from app.schemas.auth import TokenPayload
import uuid

async def test():
    async with async_session_factory() as db:
        user = TokenPayload(email='company@acme.com', user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role='company')
        try:
            res = await get_company_dashboard(user=user, db=db)
            print("Success")
        except Exception as e:
            with open('err_dash_py.txt', 'w', encoding='utf-8') as f:
                f.write(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(test())
