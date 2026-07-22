from fastapi import APIRouter

from knowledge_assistant.presentation.api.v1.auth_router import (
    router as auth_router,
)
from knowledge_assistant.presentation.api.v1.document_router import (
    router as document_router,
)
from knowledge_assistant.presentation.api.v1.job_router import (
    router as job_router,
)
from knowledge_assistant.presentation.api.v1.wiki_router import (
    router as wiki_router,
)
from knowledge_assistant.presentation.api.v1.chat_router import (
    router as chat_router,
)

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(document_router)
api_v1_router.include_router(job_router)
api_v1_router.include_router(wiki_router)
api_v1_router.include_router(chat_router)