from uuid import uuid4

import pytest

from knowledge_assistant.domain.documents.chunk_entities import (
    DocumentChunkEntity,
)
from knowledge_assistant.infrastructure.wiki.openrouter_wiki_compiler import (
    OpenRouterWikiCompiler,
    WikiClaimPayload,
    WikiCompilationPayload,
    WikiPagePayload,
)


def _chunk() -> DocumentChunkEntity:
    return DocumentChunkEntity.create(
        document_id=uuid4(),
        chunk_index=0,
        text="Supported source text.",
        page_number=1,
    )


def test_unknown_claim_sources_are_removed_without_failing_page() -> None:
    chunk = _chunk()
    payload = WikiCompilationPayload(
        pages=[
            WikiPagePayload(
                title="Supported page",
                slug="supported-page",
                summary="Summary",
                content_markdown=(
                    "Supported claim [1](citation:C1). "
                    "Unsupported claim [2](citation:C2)."
                ),
                source_chunk_ids=[chunk.id],
                claims=[
                    WikiClaimPayload(
                        claim_key="C1",
                        claim_text="Supported claim",
                        source_chunk_ids=[chunk.id],
                    ),
                    WikiClaimPayload(
                        claim_key="C2",
                        claim_text="Unsupported claim",
                        source_chunk_ids=[uuid4()],
                    ),
                ],
            )
        ]
    )

    compilation = OpenRouterWikiCompiler._to_domain(
        payload=payload,
        chunks=(chunk,),
    )

    page = compilation.pages[0]
    assert [claim.claim_key for claim in page.claims] == ["c1"]
    assert "citation:C1" in page.content_markdown
    assert "citation:C2" not in page.content_markdown
    assert "Unsupported claim [2]." in page.content_markdown


def test_page_sources_fall_back_to_valid_claim_sources() -> None:
    chunk = _chunk()
    payload = WikiCompilationPayload(
        pages=[
            WikiPagePayload(
                title="Claim-backed page",
                slug="claim-backed-page",
                summary="Summary",
                content_markdown="Claim [1](citation:C1).",
                source_chunk_ids=[uuid4()],
                claims=[
                    WikiClaimPayload(
                        claim_key="C1",
                        claim_text="Claim",
                        source_chunk_ids=[chunk.id],
                    )
                ],
            )
        ]
    )

    compilation = OpenRouterWikiCompiler._to_domain(
        payload=payload,
        chunks=(chunk,),
    )

    assert compilation.pages[0].source_chunk_ids == (chunk.id,)


def test_pages_without_any_verifiable_sources_are_rejected() -> None:
    chunk = _chunk()
    payload = WikiCompilationPayload(
        pages=[
            WikiPagePayload(
                title="Unsupported page",
                slug="unsupported-page",
                summary="Summary",
                content_markdown="Unsupported.",
                source_chunk_ids=[uuid4()],
                claims=[],
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="verifiable document sources",
    ):
        OpenRouterWikiCompiler._to_domain(
            payload=payload,
            chunks=(chunk,),
        )
