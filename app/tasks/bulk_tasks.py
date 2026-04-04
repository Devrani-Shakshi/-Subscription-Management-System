"""
Bulk operations Celery tasks.

Tasks:
    execute_bulk_operation — async execution of bulk operations.
"""

from __future__ import annotations

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


def execute_bulk_operation(
    op_type: str,
    ids: list[str],
    tenant_id: str,
    params: dict | None = None,
):
    """
    Execute a bulk operation asynchronously.

    Stores progress in Redis for polling/SSE updates.
    """
    async def _run():
        from uuid import UUID
        from app.core.database import async_session_factory
        from app.core.redis import get_redis
        from app.services.bulk.executor import BulkExecutor

        job_id = f"bulk:{tenant_id}:{op_type}:{hash(tuple(ids))}"
        redis = await get_redis()

        # Mark job as running
        await redis.set(
            job_id,
            json.dumps({"status": "running", "progress": 0}),
            ex=3600,
        )

        async with async_session_factory() as session:
            executor = BulkExecutor(session, UUID(tenant_id))
            uuid_ids = [UUID(i) for i in ids]

            result = await executor.run(
                ids=uuid_ids,
                operation_type=op_type,
                params=params,
            )

            await session.commit()

            # Store result
            await redis.set(
                job_id,
                json.dumps({
                    "status": "completed",
                    "result": result.to_dict(),
                }),
                ex=3600,
            )

            logger.info(
                "Bulk operation %s completed: %d success, %d failed",
                op_type,
                len(result.success),
                len(result.failed),
            )

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run())
    except Exception as e:
        logger.error("Bulk operation %s failed: %s", op_type, e)
    finally:
        loop.close()
