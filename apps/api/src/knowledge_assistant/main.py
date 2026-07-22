from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from knowledge_assistant.core.config import get_settings
from knowledge_assistant.infrastructure.database.session import (
    AsyncSessionFactory,
)
from knowledge_assistant.infrastructure.jobs.local_processing_worker import (
    LocalProcessingWorker,
)
from knowledge_assistant.presentation.api.exception_handlers import (
    register_exception_handlers,
)
from knowledge_assistant.presentation.api.v1.router import api_v1_router
from knowledge_assistant.presentation.middleware.security import (
    AuthRateLimitMiddleware,
    CSRFMiddleware,
)


settings = get_settings()
worker = LocalProcessingWorker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    settings.mail_outbox_directory.mkdir(parents=True, exist_ok=True)
    await worker.start()
    try:
        yield
    finally:
        await worker.stop()


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(CSRFMiddleware)
app.add_middleware(AuthRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health() -> dict[str, object]:
    async with AsyncSessionFactory() as session:
        await session.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
        "worker": "running" if worker.is_running else "stopped",
        "authentication": "cookie-session",
    }


app.include_router(api_v1_router)
