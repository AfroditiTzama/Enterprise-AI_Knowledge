from fastapi import FastAPI

from knowledge_assistant.core.config import get_settings
from knowledge_assistant.presentation.api.exception_handlers import (
    register_exception_handlers,
)
from knowledge_assistant.presentation.api.v1.router import api_v1_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    register_exception_handlers(app)
    app.include_router(api_v1_router)

    return app