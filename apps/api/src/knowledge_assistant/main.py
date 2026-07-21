from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from knowledge_assistant.core.config import get_settings
from knowledge_assistant.domain.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from knowledge_assistant.presentation.api.v1.router import (
    api_v1_router,
)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)


@app.exception_handler(AuthenticationError)
async def handle_authentication_error(
    request: Request,
    error: AuthenticationError,
) -> JSONResponse:
    del request

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": str(error),
        },
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


@app.exception_handler(AuthorizationError)
async def handle_authorization_error(
    request: Request,
    error: AuthorizationError,
) -> JSONResponse:
    del request

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": str(error),
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)
