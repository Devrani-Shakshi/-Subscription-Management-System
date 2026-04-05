import asyncio
import traceback
from app.core.database import async_session_factory
from app.routers.company import list_subscriptions
from app.schemas.auth import TokenPayload
import uuid

async def test():
    async with async_session_factory() as db:
        user = TokenPayload(email='company@acme.com', user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role='company')
        try:
            res = await list_subscriptions(user=user, db=db, page=1, limit=10, status=None)
            print("Success:", len(res['items']))
        except Exception as e:
            with open('err_subs_py.txt', 'w', encoding='utf-8') as f:
                f.write(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(test())
