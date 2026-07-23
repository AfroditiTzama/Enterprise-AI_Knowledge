import math
import re
from dataclasses import dataclass
from uuid import UUID

from knowledge_assistant.domain.chat.entities import RetrievedKnowledgeSource
from knowledge_assistant.domain.documents.chunk_entities import DocumentChunkEntity
from knowledge_assistant.domain.documents.chunk_repository import DocumentChunkRepository
from knowledge_assistant.domain.documents.repository import DocumentRepository
from knowledge_assistant.domain.embeddings.service import EmbeddingService
from knowledge_assistant.domain.retrieval.entities import (
    RetrievalDiagnostics,
    RetrievalFilters,
)
from knowledge_assistant.domain.vector_store.store import VectorStore
from knowledge_assistant.domain.wiki.entities import WikiPage
from knowledge_assistant.domain.wiki.repository import WikiRepository
from knowledge_assistant.infrastructure.retrieval.bm25 import BM25Ranker, tokenize
from knowledge_assistant.infrastructure.retrieval.context_compressor import (
    ExtractiveContextCompressor,
)
from knowledge_assistant.infrastructure.retrieval.query_rewriter import (
    LocalQueryRewriter,
)


@dataclass
class _Candidate:
    key: str
    source_type: str
    document_id: UUID | None
    title: str
    text: str
    page_number: int | None
    chunk_index: int | None
    slug: str | None
    section_title: str | None
    content_type: str | None
    parent_text: str | None
    score: float = 0.0
    vector_score: float = 0.0
    lexical_score: float = 0.0
    wiki_score: float = 0.0


@dataclass(frozen=True)
class HybridRetrievalResult:
    sources: tuple[RetrievedKnowledgeSource, ...]
    mode: str
    diagnostics: RetrievalDiagnostics


class HybridKnowledgeRetriever:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        chunk_repository: DocumentChunkRepository,
        wiki_repository: WikiRepository,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        vector_candidates: int = 18,
        lexical_candidates: int = 18,
        context_character_budget: int = 18000,
        max_sources_per_document: int = 3,
    ) -> None:
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository
        self._wiki_repository = wiki_repository
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._vector_candidates = vector_candidates
        self._lexical_candidates = lexical_candidates
        self._context_character_budget = context_character_budget
        self._max_sources_per_document = max_sources_per_document
        self._rewriter = LocalQueryRewriter()
        self._compressor = ExtractiveContextCompressor()

    async def retrieve(
        self,
        *,
        owner_id: UUID,
        question: str,
        filters: RetrievalFilters,
    ) -> HybridRetrievalResult:
        rewritten = self._rewriter.rewrite(question)
        if not rewritten:
            raise ValueError("Question cannot be empty.")

        embedding_query = "\n".join(rewritten)
        query_embedding = await self._embedding_service.embed_query(
            embedding_query
        )
        candidates: dict[str, _Candidate] = {}
        lexical_count = 0
        vector_count = 0
        wiki_count = 0

        if filters.source_scope in {"all", "documents"}:
            chunks = await self._chunk_repository.list_by_owner_id(
                owner_id=owner_id,
                document_ids=filters.document_ids,
                content_types=filters.content_types,
            )
            lexical_count = self._add_lexical_chunks(
                candidates=candidates,
                chunks=chunks,
                queries=rewritten,
            )
            vector_results = await self._vector_store.search(
                owner_id=owner_id,
                query_embedding=query_embedding,
                limit=self._vector_candidates,
                document_ids=filters.document_ids,
                content_types=filters.content_types,
            )
            vector_count = len(vector_results)
            for rank, result in enumerate(vector_results, start=1):
                key = f"chunk:{result.document_id}:{result.chunk_index}"
                candidate = candidates.get(key)
                if candidate is None:
                    candidate = _Candidate(
                        key=key,
                        source_type="document_chunk",
                        document_id=result.document_id,
                        title="Document source",
                        text=result.text,
                        page_number=result.page_number,
                        chunk_index=result.chunk_index,
                        slug=None,
                        section_title=result.section_title,
                        content_type=result.content_type,
                        parent_text=result.parent_text,
                    )
                    candidates[key] = candidate
                candidate.vector_score = max(
                    candidate.vector_score,
                    result.score,
                )
                candidate.score += self._rrf(rank)

        if filters.source_scope in {"all", "wiki"}:
            pages = await self._load_wiki_pages(
                owner_id=owner_id,
                document_ids=filters.document_ids,
            )
            wiki_count = await self._add_wiki_candidates(
                candidates=candidates,
                pages=pages,
                query_embedding=query_embedding,
                queries=rewritten,
            )

        await self._hydrate_document_titles(candidates, owner_id)
        ranked = self._rerank_and_filter(
            candidates=list(candidates.values()),
            question=question,
            limit=filters.max_sources,
        )
        sources, context_characters = self._build_sources(
            ranked=ranked,
            question=question,
        )

        source_types = {source.source_type for source in sources}
        if not sources:
            mode = "none"
        elif len(source_types) > 1:
            mode = "hybrid"
        elif "wiki" in source_types:
            mode = "wiki"
        else:
            mode = "documents"

        return HybridRetrievalResult(
            sources=sources,
            mode=mode,
            diagnostics=RetrievalDiagnostics(
                rewritten_queries=rewritten,
                lexical_candidates=lexical_count,
                vector_candidates=vector_count,
                wiki_candidates=wiki_count,
                fused_candidates=len(candidates),
                selected_sources=len(sources),
                context_characters=context_characters,
            ),
        )

    def _add_lexical_chunks(
        self,
        *,
        candidates: dict[str, _Candidate],
        chunks: list[DocumentChunkEntity],
        queries: tuple[str, ...],
    ) -> int:
        if not chunks:
            return 0
        ranker = BM25Ranker([chunk.text for chunk in chunks])
        seen: set[int] = set()
        for query in queries:
            for rank, result in enumerate(
                ranker.search(query, limit=self._lexical_candidates),
                start=1,
            ):
                chunk = chunks[result.index]
                key = f"chunk:{chunk.document_id}:{chunk.chunk_index}"
                candidate = candidates.get(key)
                if candidate is None:
                    candidate = _Candidate(
                        key=key,
                        source_type="document_chunk",
                        document_id=chunk.document_id,
                        title="Document source",
                        text=chunk.text,
                        page_number=chunk.page_number,
                        chunk_index=chunk.chunk_index,
                        slug=None,
                        section_title=chunk.section_title,
                        content_type=chunk.content_type,
                        parent_text=chunk.parent_text,
                    )
                    candidates[key] = candidate
                candidate.lexical_score = max(
                    candidate.lexical_score,
                    result.score,
                )
                candidate.score += self._rrf(rank)
                seen.add(result.index)
        return len(seen)

    async def _load_wiki_pages(
        self,
        *,
        owner_id: UUID,
        document_ids: tuple[UUID, ...],
    ) -> list[WikiPage]:
        if not document_ids:
            return await self._wiki_repository.list_by_owner_id(owner_id)
        pages: dict[UUID, WikiPage] = {}
        for document_id in document_ids:
            for page in await self._wiki_repository.list_by_document_id(
                owner_id=owner_id,
                document_id=document_id,
            ):
                pages[page.id] = page
        return list(pages.values())

    async def _add_wiki_candidates(
        self,
        *,
        candidates: dict[str, _Candidate],
        pages: list[WikiPage],
        query_embedding: list[float],
        queries: tuple[str, ...],
    ) -> int:
        if not pages:
            return 0
        texts = [self._wiki_text(page) for page in pages]
        embeddings = await self._embedding_service.embed_documents(texts)
        semantic_ranked: list[tuple[int, float]] = []
        for index, embedding in enumerate(embeddings):
            score = self._cosine_similarity(query_embedding, embedding)
            if score > 0.15:
                semantic_ranked.append((index, score))
        semantic_ranked.sort(key=lambda item: item[1], reverse=True)

        ranker = BM25Ranker(texts)
        lexical_ranks: dict[int, int] = {}
        for query in queries:
            for rank, result in enumerate(
                ranker.search(query, limit=self._lexical_candidates),
                start=1,
            ):
                lexical_ranks[result.index] = min(
                    rank,
                    lexical_ranks.get(result.index, rank),
                )

        selected_indexes: set[int] = set()
        for rank, (index, score) in enumerate(semantic_ranked[:12], start=1):
            page = pages[index]
            key = f"wiki:{page.id}"
            candidate = candidates.setdefault(
                key,
                _Candidate(
                    key=key,
                    source_type="wiki",
                    document_id=page.document_id,
                    title=page.title,
                    text=texts[index],
                    page_number=None,
                    chunk_index=None,
                    slug=page.slug,
                    section_title=None,
                    content_type="wiki",
                    parent_text=None,
                ),
            )
            candidate.wiki_score = max(candidate.wiki_score, score)
            candidate.score += self._rrf(rank)
            selected_indexes.add(index)

        for index, rank in lexical_ranks.items():
            page = pages[index]
            key = f"wiki:{page.id}"
            candidate = candidates.setdefault(
                key,
                _Candidate(
                    key=key,
                    source_type="wiki",
                    document_id=page.document_id,
                    title=page.title,
                    text=texts[index],
                    page_number=None,
                    chunk_index=None,
                    slug=page.slug,
                    section_title=None,
                    content_type="wiki",
                    parent_text=None,
                ),
            )
            candidate.score += self._rrf(rank)
            selected_indexes.add(index)
        return len(selected_indexes)

    async def _hydrate_document_titles(
        self,
        candidates: dict[str, _Candidate],
        owner_id: UUID,
    ) -> None:
        titles: dict[UUID, str] = {}
        for candidate in candidates.values():
            document_id = candidate.document_id
            if candidate.source_type == "wiki" or document_id is None:
                continue
            if document_id not in titles:
                document = await self._document_repository.get_by_id(document_id)
                titles[document_id] = (
                    document.original_filename
                    if document is not None and document.owner_id == owner_id
                    else "Document source"
                )
            candidate.title = titles[document_id]

    def _rerank_and_filter(
        self,
        *,
        candidates: list[_Candidate],
        question: str,
        limit: int,
    ) -> list[_Candidate]:
        query_terms = set(tokenize(question))
        for candidate in candidates:
            haystack = " ".join(
                value
                for value in (
                    candidate.title,
                    candidate.section_title or "",
                    candidate.text[:2500],
                )
                if value
            )
            terms = set(tokenize(haystack))
            overlap = len(query_terms & terms) / max(len(query_terms), 1)
            title_terms = set(tokenize(candidate.title))
            title_overlap = len(query_terms & title_terms) / max(
                len(query_terms), 1
            )
            candidate.score += overlap * 0.08 + title_overlap * 0.05
            candidate.score += max(candidate.vector_score, 0.0) * 0.03
            candidate.score += max(candidate.wiki_score, 0.0) * 0.02

        candidates.sort(key=lambda item: item.score, reverse=True)
        selected: list[_Candidate] = []
        per_document: dict[UUID, int] = {}
        normalized_texts: list[set[str]] = []

        for candidate in candidates:
            if candidate.document_id is not None:
                current = per_document.get(candidate.document_id, 0)
                if current >= self._max_sources_per_document:
                    continue

            tokens = set(tokenize(candidate.text[:4000]))
            duplicate = any(
                self._jaccard(tokens, existing) >= 0.88
                for existing in normalized_texts
            )
            if duplicate:
                continue

            selected.append(candidate)
            normalized_texts.append(tokens)
            if candidate.document_id is not None:
                per_document[candidate.document_id] = (
                    per_document.get(candidate.document_id, 0) + 1
                )
            if len(selected) >= limit:
                break
        return selected

    def _build_sources(
        self,
        *,
        ranked: list[_Candidate],
        question: str,
    ) -> tuple[tuple[RetrievedKnowledgeSource, ...], int]:
        if not ranked:
            return (), 0
        remaining = self._context_character_budget
        sources: list[RetrievedKnowledgeSource] = []
        for candidate in ranked:
            source_budget = max(
                900,
                min(5000, remaining // max(len(ranked) - len(sources), 1)),
            )
            expanded = candidate.parent_text or candidate.text
            compressed = self._compressor.compress(
                text=expanded,
                query=question,
                max_characters=source_budget,
            )
            if not compressed:
                continue
            sources.append(
                RetrievedKnowledgeSource(
                    source_id=f"S{len(sources) + 1}",
                    source_type=candidate.source_type,
                    document_id=candidate.document_id,
                    title=candidate.title,
                    text=compressed,
                    score=max(0.0, min(candidate.score * 10, 1.0)),
                    slug=candidate.slug,
                    page_number=candidate.page_number,
                    chunk_index=candidate.chunk_index,
                    section_title=candidate.section_title,
                    content_type=candidate.content_type,
                )
            )
            remaining -= len(compressed)
            if remaining <= 0:
                break
        return tuple(sources), self._context_character_budget - max(remaining, 0)

    @staticmethod
    def _wiki_text(page: WikiPage) -> str:
        return "\n\n".join(
            value for value in (page.title, page.summary, page.content_markdown)
            if value.strip()
        )

    @staticmethod
    def _rrf(rank: int, constant: int = 60) -> float:
        return 1.0 / (constant + rank)

    @staticmethod
    def _jaccard(first: set[str], second: set[str]) -> float:
        if not first or not second:
            return 0.0
        return len(first & second) / len(first | second)

    @staticmethod
    def _cosine_similarity(first: list[float], second: list[float]) -> float:
        if len(first) != len(second):
            return 0.0
        dot = sum(left * right for left, right in zip(first, second, strict=True))
        denominator = math.sqrt(sum(value * value for value in first)) * math.sqrt(
            sum(value * value for value in second)
        )
        return dot / denominator if denominator else 0.0
