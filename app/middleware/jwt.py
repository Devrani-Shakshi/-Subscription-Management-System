"""
JWT middleware — verify Bearer token and set request.state.user.

Skips public paths: /auth/*, /public/*, /docs, /openapi.json
"""

from __future__ import annotations

import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.security import decode_token
from app.schemas.auth import TokenPayload


# Paths that do NOT require a JWT
_PUBLIC_PREFIXES = ("/auth/", "/public/", "/docs", "/openapi.json", "/redoc", "/health")


class JWTMiddleware(BaseHTTPMiddleware):
    """Decode Bearer token → request.state.user (TokenPayload)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Skip public endpoints
        if any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            request.state.user = None
            return await call_next(request)

        # OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"code": "AUTH_ERROR", "message": "Missing token."},
            )

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"code": "AUTH_ERROR", "message": "Invalid or expired token."},
            )

        if payload.get("type") != "access":
            return JSONResponse(
                status_code=401,
                content={"code": "AUTH_ERROR", "message": "Invalid token type."},
            )

        tenant_id_raw = payload.get("tenant_id")
        request.state.user = TokenPayload(
            user_id=uuid.UUID(payload["sub"]),
            role=payload["role"],
            tenant_id=uuid.UUID(tenant_id_raw) if tenant_id_raw else None,
            email=payload["email"],
        )
        return await call_next(request)
