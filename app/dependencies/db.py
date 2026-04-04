"""
Database session dependency for FastAPI.

Every request gets an ``AsyncSession`` that:
1. Sets ``app.tenant_id`` via PostgreSQL ``SET`` so that RLS policies
   activate for the correct tenant.
2. Commits on success, rolls back on exception.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory


async def get_db(
    tenant_id: uuid.UUID | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a scoped async DB session.

    Parameters
    ----------
    tenant_id:
        The tenant UUID from the JWT / middleware.
        ``None`` for super_admin (sets ``app.tenant_id = 'SUPER'``).
    """
    async with async_session_factory() as session:
        try:
            rls_value = str(tenant_id) if tenant_id else "SUPER"
            await session.execute(
                text("SET LOCAL app.tenant_id = :tid"),
                {"tid": rls_value},
            )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_no_tenant() -> AsyncGenerator[AsyncSession, None]:
    """
    Session without RLS for auth endpoints (login, register) where
    no tenant context exists yet.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
