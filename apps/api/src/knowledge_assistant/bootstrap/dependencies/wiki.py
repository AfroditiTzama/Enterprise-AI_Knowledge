import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_assistant.application.wiki.commands.compile_document_wiki import (
    CompileDocumentWikiCommand,
)
from knowledge_assistant.application.wiki.commands.scan_wiki_maintenance import (
    ScanWikiMaintenanceCommand,
)
from knowledge_assistant.bootstrap.dependencies.document import (
    get_document_chunk_repository,
    get_document_repository,
    get_embedding_service,
)
from knowledge_assistant.domain.documents.chunk_repository import (
    DocumentChunkRepository,
)
from knowledge_assistant.domain.documents.repository import (
    DocumentRepository,
)
from knowledge_assistant.domain.embeddings.service import (
    EmbeddingService,
)
from knowledge_assistant.domain.wiki.compiler import WikiCompiler
from knowledge_assistant.domain.wiki.matcher import (
    WikiSemanticMatcher,
)
from knowledge_assistant.domain.wiki.merger import WikiPageMerger
from knowledge_assistant.domain.wiki.repository import WikiRepository
from knowledge_assistant.infrastructure.database.repositories.wiki_repository import (
    SQLAlchemyWikiRepository,
)
from knowledge_assistant.infrastructure.database.session import (
    get_db_session,
)
from knowledge_assistant.application.wiki.services.semantic_matcher import (
    EmbeddingWikiSemanticMatcher,
)
from knowledge_assistant.infrastructure.wiki.openrouter_wiki_compiler import (
    OpenRouterWikiCompiler,
)
from knowledge_assistant.infrastructure.wiki.openrouter_wiki_merger import (
    OpenRouterWikiPageMerger,
)


def get_wiki_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> WikiRepository:
    return SQLAlchemyWikiRepository(session)


@lru_cache
def get_wiki_compiler() -> WikiCompiler:
    api_key = os.getenv(
        "OPENROUTER_API_KEY",
        "",
    ).strip()

    model = os.getenv(
        "OPENROUTER_MODEL",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    if not model:
        raise RuntimeError(
            "OPENROUTER_MODEL is not configured."
        )

    return OpenRouterWikiCompiler(
        api_key=api_key,
        model=model,
    )



@lru_cache
def get_wiki_page_merger() -> WikiPageMerger:
    api_key = os.getenv(
        "OPENROUTER_API_KEY",
        "",
    ).strip()

    model = os.getenv(
        "OPENROUTER_MODEL",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    if not model:
        raise RuntimeError(
            "OPENROUTER_MODEL is not configured."
        )

    return OpenRouterWikiPageMerger(
        api_key=api_key,
        model=model,
    )


def get_wiki_semantic_matcher(
    embedding_service: Annotated[
        EmbeddingService,
        Depends(get_embedding_service),
    ],
) -> WikiSemanticMatcher:
    return EmbeddingWikiSemanticMatcher(
        embedding_service=embedding_service,
        candidate_threshold=0.82,
    )

def get_compile_document_wiki_command(
    document_repository: Annotated[
        DocumentRepository,
        Depends(get_document_repository),
    ],
    document_chunk_repository: Annotated[
        DocumentChunkRepository,
        Depends(get_document_chunk_repository),
    ],
    wiki_repository: Annotated[
        WikiRepository,
        Depends(get_wiki_repository),
    ],
    wiki_compiler: Annotated[
        WikiCompiler,
        Depends(get_wiki_compiler),
    ],
    wiki_semantic_matcher: Annotated[
        WikiSemanticMatcher,
        Depends(get_wiki_semantic_matcher),
    ],
    wiki_page_merger: Annotated[
        WikiPageMerger,
        Depends(get_wiki_page_merger),
    ],
) -> CompileDocumentWikiCommand:
    return CompileDocumentWikiCommand(
        document_repository=document_repository,
        document_chunk_repository=document_chunk_repository,
        wiki_repository=wiki_repository,
        wiki_compiler=wiki_compiler,
        wiki_semantic_matcher=wiki_semantic_matcher,
        wiki_page_merger=wiki_page_merger,
    )


WikiRepositoryDependency = Annotated[
    WikiRepository,
    Depends(get_wiki_repository),
]

CompileDocumentWikiCommandDependency = Annotated[
    CompileDocumentWikiCommand,
    Depends(get_compile_document_wiki_command),
]

def get_scan_wiki_maintenance_command(
    wiki_repository: Annotated[
        WikiRepository,
        Depends(get_wiki_repository),
    ],
) -> ScanWikiMaintenanceCommand:
    return ScanWikiMaintenanceCommand(wiki_repository)


ScanWikiMaintenanceCommandDependency = Annotated[
    ScanWikiMaintenanceCommand,
    Depends(get_scan_wiki_maintenance_command),
]
