from uuid import uuid4

from knowledge_assistant.application.wiki.commands.compile_document_wiki import (
    CompileDocumentWikiCommand,
)
from knowledge_assistant.domain.wiki.compiler import (
    WikiClaimDraft,
    WikiPageDraft,
)


def test_claim_keys_are_namespaced_per_document() -> None:
    document_id = uuid4()
    chunk_id = uuid4()
    draft = WikiPageDraft(
        title="Citations",
        slug="citations",
        summary="Summary",
        content_markdown=(
            "A supported statement. [C1](citation:C1)"
        ),
        source_chunk_ids=(chunk_id,),
        related_page_slugs=(),
        claims=(
            WikiClaimDraft(
                claim_key="C1",
                claim_text="A supported statement.",
                source_chunk_ids=(chunk_id,),
            ),
        ),
    )

    updated = CompileDocumentWikiCommand._namespace_draft_citations(
        draft=draft,
        document_id=document_id,
    )

    expected_key = f"{document_id.hex[:8]}-citations-c1"
    assert updated.claims[0].claim_key == expected_key
    assert f"citation:{expected_key}" in updated.content_markdown
