from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from knowledge_assistant.core.config import get_settings
from knowledge_assistant.presentation.api.v1.router import (
    api_v1_router,
)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)