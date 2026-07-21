from datetime import datetime, timezone
from uuid import uuid4

import pytest

from knowledge_assistant.application.wiki.services.semantic_matcher import (
    EmbeddingWikiSemanticMatcher,
)
from knowledge_assistant.domain.embeddings.service import (
    EmbeddingService,
)
from knowledge_assistant.domain.wiki.compiler import (
    WikiPageDraft,
)
from knowledge_assistant.domain.wiki.entities import WikiPage
from knowledge_assistant.domain.wiki.matcher import (
    WikiMatchDecision,
)


class FakeEmbeddingService(EmbeddingService):
    def __init__(self) -> None:
        self.was_called = False

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        self.was_called = True

        vectors: list[list[float]] = []

        for text in texts:
            normalized = text.lower()

            if (
                "authentication" in normalized
                or "jwt" in normalized
                or "token" in normalized
            ):
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])

        return vectors

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        return [1.0, 0.0]


def create_page(
    *,
    slug: str,
    title: str,
    summary: str,
) -> WikiPage:
    now = datetime.now(timezone.utc)

    return WikiPage(
        id=uuid4(),
        owner_id=uuid4(),
        document_id=None,
        slug=slug,
        title=title,
        summary=summary,
        content_markdown="Content.",
        created_at=now,
        updated_at=now,
    )


def create_draft(
    *,
    slug: str,
    title: str,
    summary: str,
) -> WikiPageDraft:
    return WikiPageDraft(
        slug=slug,
        title=title,
        summary=summary,
        content_markdown="Content.",
        source_chunk_ids=(uuid4(),),
        related_page_slugs=(),
    )


@pytest.mark.asyncio
async def test_exact_match_does_not_require_embeddings() -> None:
    embedding_service = FakeEmbeddingService()

    matcher = EmbeddingWikiSemanticMatcher(
        embedding_service=embedding_service,
    )

    page = create_page(
        slug="authentication",
        title="Authentication",
        summary="Login flow.",
    )

    draft = create_draft(
        slug="authentication",
        title="Authentication",
        summary="Updated login flow.",
    )

    result = await matcher.match(
        drafts=(draft,),
        existing_pages=(page,),
    )

    assert result[0].decision == (
        WikiMatchDecision.EXACT_MATCH
    )
    assert result[0].matched_page_id == page.id
    assert result[0].score == 1.0
    assert embedding_service.was_called is False


@pytest.mark.asyncio
async def test_semantic_candidate_is_detected() -> None:
    matcher = EmbeddingWikiSemanticMatcher(
        embedding_service=FakeEmbeddingService(),
        candidate_threshold=0.82,
    )

    page = create_page(
        slug="jwt-authentication",
        title="JWT Authentication",
        summary="Authentication using JWT tokens.",
    )

    draft = create_draft(
        slug="token-based-login",
        title="Token Authentication",
        summary="Login using access tokens.",
    )

    result = await matcher.match(
        drafts=(draft,),
        existing_pages=(page,),
    )

    assert result[0].decision == (
        WikiMatchDecision.SEMANTIC_CANDIDATE
    )
    assert result[0].matched_page_id == page.id
    assert result[0].score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_unrelated_page_is_marked_for_creation() -> None:
    matcher = EmbeddingWikiSemanticMatcher(
        embedding_service=FakeEmbeddingService(),
        candidate_threshold=0.82,
    )

    page = create_page(
        slug="authentication",
        title="Authentication",
        summary="Login flow.",
    )

    draft = create_draft(
        slug="billing",
        title="Billing",
        summary="Invoice information.",
    )

    result = await matcher.match(
        drafts=(draft,),
        existing_pages=(page,),
    )

    assert result[0].decision == (
        WikiMatchDecision.CREATE
    )
