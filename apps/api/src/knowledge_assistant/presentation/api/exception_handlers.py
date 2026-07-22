from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from knowledge_assistant.domain.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolation,
    ConflictError,
    DomainError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


def register_exception_handlers(app: FastAPI) -> None:
    def response(code: int, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=code,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        del request
        return response(status.HTTP_400_BAD_REQUEST, exc)

    @app.exception_handler(BusinessRuleViolation)
    async def business_rule_handler(
        request: Request,
        exc: BusinessRuleViolation,
    ) -> JSONResponse:
        del request
        return response(status.HTTP_400_BAD_REQUEST, exc)

    @app.exception_handler(ConflictError)
    async def conflict_error_handler(
        request: Request,
        exc: ConflictError,
    ) -> JSONResponse:
        del request
        return response(status.HTTP_409_CONFLICT, exc)

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(
        request: Request,
        exc: NotFoundError,
    ) -> JSONResponse:
        del request
        return response(status.HTTP_404_NOT_FOUND, exc)

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(
        request: Request,
        exc: RateLimitError,
    ) -> JSONResponse:
        del request
        result = response(status.HTTP_429_TOO_MANY_REQUESTS, exc)
        result.headers["Retry-After"] = "60"
        return result

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request,
        exc: AuthenticationError,
    ) -> JSONResponse:
        del request
        result = response(status.HTTP_401_UNAUTHORIZED, exc)
        result.headers["WWW-Authenticate"] = "Bearer"
        return result

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request,
        exc: AuthorizationError,
    ) -> JSONResponse:
        del request
        return response(status.HTTP_403_FORBIDDEN, exc)

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        del request
        return response(status.HTTP_400_BAD_REQUEST, exc)
