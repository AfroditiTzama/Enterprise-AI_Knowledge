import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from knowledge_assistant.application.chat.queries.ask_knowledge import (
    AskKnowledgeQuery,
)
from knowledge_assistant.bootstrap.dependencies.document import (
    get_document_repository,
    get_embedding_service,
    get_vector_store,
)
from knowledge_assistant.bootstrap.dependencies.wiki import (
    get_wiki_repository,
)
from knowledge_assistant.domain.chat.answer_generator import (
    KnowledgeAnswerGenerator,
)
from knowledge_assistant.domain.documents.repository import (
    DocumentRepository,
)
from knowledge_assistant.domain.embeddings.service import (
    EmbeddingService,
)
from knowledge_assistant.domain.vector_store.store import (
    VectorStore,
)
from knowledge_assistant.domain.wiki.repository import (
    WikiRepository,
)
from knowledge_assistant.infrastructure.chat.openrouter_answer_generator import (
    OpenRouterKnowledgeAnswerGenerator,
)


@lru_cache
def get_knowledge_answer_generator(
) -> KnowledgeAnswerGenerator:
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

    return OpenRouterKnowledgeAnswerGenerator(
        api_key=api_key,
        model=model,
    )


def get_ask_knowledge_query(
    document_repository: Annotated[
        DocumentRepository,
        Depends(get_document_repository),
    ],
    wiki_repository: Annotated[
        WikiRepository,
        Depends(get_wiki_repository),
    ],
    embedding_service: Annotated[
        EmbeddingService,
        Depends(get_embedding_service),
    ],
    vector_store: Annotated[
        VectorStore,
        Depends(get_vector_store),
    ],
    answer_generator: Annotated[
        KnowledgeAnswerGenerator,
        Depends(get_knowledge_answer_generator),
    ],
) -> AskKnowledgeQuery:
    return AskKnowledgeQuery(
        document_repository=document_repository,
        wiki_repository=wiki_repository,
        embedding_service=embedding_service,
        vector_store=vector_store,
        answer_generator=answer_generator,
    )


AskKnowledgeQueryDependency = Annotated[
    AskKnowledgeQuery,
    Depends(get_ask_knowledge_query),
]