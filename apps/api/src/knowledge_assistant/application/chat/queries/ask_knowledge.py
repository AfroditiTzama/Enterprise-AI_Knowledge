import math
from uuid import UUID

from knowledge_assistant.domain.chat.answer_generator import (
    KnowledgeAnswerGenerator,
)
from knowledge_assistant.domain.chat.entities import (
    KnowledgeChatResult,
    RetrievedKnowledgeSource,
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
from knowledge_assistant.domain.wiki.entities import WikiPage
from knowledge_assistant.domain.wiki.repository import (
    WikiRepository,
)


class AskKnowledgeQuery:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        wiki_repository: WikiRepository,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        answer_generator: KnowledgeAnswerGenerator,
        max_wiki_pages: int = 3,
        max_vector_chunks: int = 4,
        minimum_wiki_score: float = 0.20,
        vector_fallback_threshold: float = 0.45,
        minimum_vector_score: float = 0.15,
    ) -> None:
        self._document_repository = document_repository
        self._wiki_repository = wiki_repository
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._answer_generator = answer_generator
        self._max_wiki_pages = max_wiki_pages
        self._max_vector_chunks = max_vector_chunks
        self._minimum_wiki_score = minimum_wiki_score
        self._vector_fallback_threshold = (
            vector_fallback_threshold
        )
        self._minimum_vector_score = minimum_vector_score

    async def execute(
        self,
        *,
        owner_id: UUID,
        question: str,
        assistant_behavior: str = "balanced",
        preferred_language: str = "en",
    ) -> KnowledgeChatResult:
        cleaned_question = question.strip()

        if not cleaned_question:
            raise ValueError(
                "Question cannot be empty."
            )

        query_embedding = (
            await self._embedding_service.embed_query(
                cleaned_question
            )
        )

        wiki_pages = (
            await self._wiki_repository.list_by_owner_id(
                owner_id
            )
        )

        wiki_candidates = await self._rank_wiki_pages(
            pages=wiki_pages,
            query_embedding=query_embedding,
        )

        sources: list[RetrievedKnowledgeSource] = []

        for page, page_text, score in wiki_candidates:
            sources.append(
                RetrievedKnowledgeSource(
                    source_id=f"S{len(sources) + 1}",
                    source_type="wiki",
                    document_id=page.document_id,
                    title=page.title,
                    slug=page.slug,
                    text=page_text,
                    score=score,
                )
            )

        best_wiki_score = (
            wiki_candidates[0][2]
            if wiki_candidates
            else 0.0
        )

        use_vector_fallback = (
            not wiki_candidates
            or best_wiki_score
            < self._vector_fallback_threshold
        )

        vector_sources_added = False

        if use_vector_fallback:
            vector_results = await self._vector_store.search(
                owner_id=owner_id,
                query_embedding=query_embedding,
                limit=self._max_vector_chunks,
            )

            document_titles: dict[UUID, str] = {}

            for result in vector_results:
                if result.score < self._minimum_vector_score:
                    continue

                if result.document_id not in document_titles:
                    document = (
                        await self._document_repository.get_by_id(
                            result.document_id
                        )
                    )

                    if (
                        document is not None
                        and document.owner_id == owner_id
                    ):
                        document_titles[result.document_id] = (
                            document.original_filename
                        )
                    else:
                        document_titles[result.document_id] = (
                            "Document source"
                        )

                sources.append(
                    RetrievedKnowledgeSource(
                        source_id=f"S{len(sources) + 1}",
                        source_type="document_chunk",
                        document_id=result.document_id,
                        title=document_titles[
                            result.document_id
                        ],
                        text=result.text,
                        page_number=result.page_number,
                        chunk_index=result.chunk_index,
                        score=result.score,
                    )
                )

                vector_sources_added = True

        if not sources:
            return KnowledgeChatResult(
                answer_markdown=(
                    "Δεν βρέθηκαν σχετικές πληροφορίες στα "
                    "διαθέσιμα έγγραφα."
                ),
                retrieval_mode="none",
                sources=(),
            )

        generated_answer = (
            await self._answer_generator.generate(
                question=cleaned_question,
                sources=tuple(sources),
                assistant_behavior=assistant_behavior,
                preferred_language=preferred_language,
            )
        )

        visible_sources = self._select_visible_sources(
            sources=tuple(sources),
            used_source_ids=(
                generated_answer.used_source_ids
            ),
        )

        wiki_sources_added = bool(wiki_candidates)

        if wiki_sources_added and vector_sources_added:
            retrieval_mode = "hybrid"
        elif wiki_sources_added:
            retrieval_mode = "wiki"
        else:
            retrieval_mode = "vector"

        return KnowledgeChatResult(
            answer_markdown=(
                generated_answer.answer_markdown
            ),
            retrieval_mode=retrieval_mode,
            sources=visible_sources,
        )

    async def _rank_wiki_pages(
        self,
        *,
        pages: list[WikiPage],
        query_embedding: list[float],
    ) -> list[tuple[WikiPage, str, float]]:
        if not pages:
            return []

        page_texts = [
            self._format_wiki_page(page)
            for page in pages
        ]

        page_embeddings = (
            await self._embedding_service.embed_documents(
                page_texts
            )
        )

        if len(page_embeddings) != len(pages):
            raise ValueError(
                "Wiki embedding count does not match page count."
            )

        ranked_pages: list[
            tuple[WikiPage, str, float]
        ] = []

        for page, page_text, page_embedding in zip(
            pages,
            page_texts,
            page_embeddings,
            strict=True,
        ):
            score = self._cosine_similarity(
                query_embedding,
                page_embedding,
            )

            if score < self._minimum_wiki_score:
                continue

            ranked_pages.append(
                (
                    page,
                    page_text,
                    score,
                )
            )

        ranked_pages.sort(
            key=lambda item: item[2],
            reverse=True,
        )

        return ranked_pages[:self._max_wiki_pages]

    @staticmethod
    def _format_wiki_page(
        page: WikiPage,
    ) -> str:
        return "\n\n".join(
            part
            for part in (
                page.title,
                page.summary,
                page.content_markdown,
            )
            if part.strip()
        )

    @staticmethod
    def _cosine_similarity(
        first: list[float],
        second: list[float],
    ) -> float:
        if len(first) != len(second):
            raise ValueError(
                "Embedding dimensions do not match."
            )

        dot_product = sum(
            left * right
            for left, right in zip(
                first,
                second,
                strict=True,
            )
        )

        first_norm = math.sqrt(
            sum(value * value for value in first)
        )

        second_norm = math.sqrt(
            sum(value * value for value in second)
        )

        denominator = first_norm * second_norm

        if denominator == 0:
            return 0.0

        return dot_product / denominator

    @staticmethod
    def _select_visible_sources(
        *,
        sources: tuple[RetrievedKnowledgeSource, ...],
        used_source_ids: tuple[str, ...],
    ) -> tuple[RetrievedKnowledgeSource, ...]:
        if not used_source_ids:
            return sources

        used_source_id_set = set(used_source_ids)

        selected_sources = tuple(
            source
            for source in sources
            if source.source_id in used_source_id_set
        )

        return selected_sources or sources