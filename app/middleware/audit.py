"""
Audit middleware — log every mutating request as a BackgroundTask.
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Post-response hook: log mutating operations."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        if request.method in _MUTATING_METHODS:
            user = getattr(request.state, "user", None)
            user_email = user.email if user else "anonymous"
            tenant = getattr(request.state, "tenant", None)
            logger.info(
                "AUDIT | %s %s | user=%s tenant=%s status=%d",
                request.method,
                request.url.path,
                user_email,
                tenant,
                response.status_code,
            )

        return response
