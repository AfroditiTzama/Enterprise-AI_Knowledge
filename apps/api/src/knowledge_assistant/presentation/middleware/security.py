import asyncio
import time
from collections import defaultdict, deque
from uuid import UUID

import jwt
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from knowledge_assistant.core.config import get_settings
from knowledge_assistant.domain.auth.security import secrets_match
from knowledge_assistant.infrastructure.auth.jwt_token_service import (
    JWTTokenService,
)
from knowledge_assistant.infrastructure.database.repositories.auth_repository import (
    SQLAlchemyAuthRepository,
)
from knowledge_assistant.infrastructure.database.session import (
    AsyncSessionFactory,
)


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    _LIMITED_PATHS = {
        "/auth/login",
        "/auth/register",
        "/auth/password-reset/request",
        "/auth/password-reset/confirm",
        "/auth/email-verification/request",
    }

    def __init__(self, app) -> None:
        super().__init__(app)
        settings = get_settings()
        self._limit = settings.auth_rate_limit_requests
        self._window = settings.auth_rate_limit_window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path not in self._LIMITED_PATHS:
            return await call_next(request)

        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = (
            forwarded_for.split(",", 1)[0].strip()
            if forwarded_for
            else request.client.host if request.client else "unknown"
        )
        key = f"{request.url.path}:{client_ip}"
        now = time.monotonic()

        async with self._lock:
            bucket = self._requests[key]
            while bucket and now - bucket[0] > self._window:
                bucket.popleft()
            if len(bucket) >= self._limit:
                retry_after = max(
                    1,
                    int(self._window - (now - bucket[0])),
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": (
                            "Too many requests. Please wait before trying again."
                        )
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            bucket.append(now)

        return await call_next(request)


class CSRFMiddleware(BaseHTTPMiddleware):
    _SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    _EXEMPT_PATHS = {
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
        "/auth/logout",
        "/auth/password-reset/request",
        "/auth/password-reset/confirm",
        "/auth/email-verification/confirm",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        if (
            request.method in self._SAFE_METHODS
            or request.url.path in self._EXEMPT_PATHS
            or request.headers.get("authorization")
        ):
            return await call_next(request)

        settings = get_settings()
        access_token = request.cookies.get(settings.access_cookie_name)
        if not access_token:
            return await call_next(request)

        csrf_token = request.headers.get("x-csrf-token")
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token was not provided."},
            )

        try:
            payload = JWTTokenService().verify_token(access_token)
            if payload.get("type") != "access":
                raise ValueError("unexpected token type")
            session_id = UUID(str(payload.get("sid")))
        except (jwt.PyJWTError, ValueError, TypeError):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Session token is invalid or expired."},
            )

        async with AsyncSessionFactory() as session:
            repository = SQLAlchemyAuthRepository(session)
            auth_session = await repository.get_session(session_id)

        if (
            auth_session is None
            or not auth_session.is_active()
            or not secrets_match(
                csrf_token,
                auth_session.csrf_token_hash,
            )
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token is invalid."},
            )

        return await call_next(request)
