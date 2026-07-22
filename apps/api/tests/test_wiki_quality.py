from datetime import datetime, timezone
from uuid import uuid4

from knowledge_assistant.application.wiki.services.quality import (
    calculate_wiki_quality,
)
from knowledge_assistant.domain.wiki.entities import (
    WikiClaimReference,
    WikiPage,
    WikiPageDetails,
    WikiPageReference,
    WikiPageSourceReference,
)


def _details(content: str) -> WikiPageDetails:
    now = datetime.now(timezone.utc)
    page = WikiPage(
        id=uuid4(),
        owner_id=uuid4(),
        document_id=None,
        slug="quality-page",
        title="Quality page",
        summary="Quality summary",
        content_markdown=content,
        created_at=now,
        updated_at=now,
    )
    source = WikiPageSourceReference(
        chunk_id=uuid4(),
        document_id=uuid4(),
        document_filename="source.pdf",
        chunk_index=0,
        page_number=1,
    )
    related = WikiPageReference(
        page_id=uuid4(),
        slug="related",
        title="Related",
        label="related",
    )
    claim = WikiClaimReference(
        claim_key="abc-c1",
        claim_text="A factual paragraph contains enough words.",
        position=0,
        sources=(source,),
    )
    return WikiPageDetails(
        page=page,
        sources=(source,),
        related_pages=(related,),
        backlinks=(),
        claim_citations=(claim,),
    )


def test_quality_detects_supported_and_unsupported_blocks() -> None:
    details = _details(
        "A factual paragraph contains enough words to be evaluated and "
        "has a source citation. [C1](citation:abc-c1)\n\n"
        "Another factual paragraph contains enough words but does not "
        "include any source citation marker."
    )

    quality = calculate_wiki_quality(details)

    assert quality.supported_claims == 1
    assert quality.unsupported_claims == 1
    assert quality.source_coverage == 50
    assert quality.connections_count == 1
    assert quality.overall < 100
