"""
FastAPI application factory.

Middleware registration order (outermost → innermost):
  1. AuditMiddleware   — post-response logging
  2. TenantMiddleware  — set request.state.tenant
  3. JWTMiddleware     — verify token → request.state.user

Router registration:
  /auth/*   — public
  /public/* — public
  /admin/*  — super_admin only (Depends guard)
  /company/* — company only (Depends guard)
  /portal/* — portal_user only (Depends guard)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis import close_redis
from app.exceptions.handlers import register_exception_handlers
from app.middleware.audit import AuditMiddleware
from app.middleware.jwt import JWTMiddleware
from app.middleware.tenant import TenantMiddleware

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown lifecycle."""
    from app.core.redis import get_redis
    # Eagerly initialize Redis (to trigger fallback if it's down)
    await get_redis()
    yield
    await close_redis()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Middleware stack (reverse order = innermost first) ────────
    # Starlette applies middleware in LIFO order, so we add them
    # in reverse: last added = outermost = runs first.
    app.add_middleware(AuditMiddleware)    # 3rd: post-response audit
    app.add_middleware(TenantMiddleware)   # 2nd: set tenant context
    app.add_middleware(JWTMiddleware)      # 1st: verify JWT

    # ── Exception handlers ───────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────
    from app.routers.auth import router as auth_router
    from app.routers.admin import router as admin_router
    from app.routers.company import router as company_router
    from app.routers.portal import router as portal_router
    from app.routers.public import router as public_router

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(company_router)
    app.include_router(portal_router)
    app.include_router(public_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
 
