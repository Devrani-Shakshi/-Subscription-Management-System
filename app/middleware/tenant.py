"""
Tenant middleware — set request.state.tenant + DB RLS context.

Runs AFTER JWTMiddleware so request.state.user is available.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Set tenant context based on JWT role:
      super_admin  → tenant = None
      company      → tenant = jwt.tenant_id
      portal_user  → tenant = jwt.tenant_id
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        user = getattr(request.state, "user", None)

        if user is None:
            # Public endpoint — no tenant context
            request.state.tenant = None
        elif user.role == "super_admin":
            request.state.tenant = None
        else:
            # company or portal_user — tenant is their tenant_id
            request.state.tenant = user.tenant_id

        return await call_next(request)
