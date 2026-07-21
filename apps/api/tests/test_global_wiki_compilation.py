from datetime import datetime, timezone
from uuid import uuid4

from knowledge_assistant.application.wiki.commands.compile_document_wiki import (
    CompileDocumentWikiCommand,
)
from knowledge_assistant.domain.wiki.entities import (
    WikiPage,
)


def test_global_slug_has_no_document_prefix() -> None:
    slug = CompileDocumentWikiCommand._create_global_slug(
        draft_slug="  JWT Authentication  ",
    )

    assert slug == "jwt-authentication"


def test_existing_page_becomes_global_and_keeps_identity() -> None:
    page_id = uuid4()
    owner_id = uuid4()
    document_id = uuid4()
    created_at = datetime.now(timezone.utc)

    existing_page = WikiPage(
        id=page_id,
        owner_id=owner_id,
        document_id=document_id,
        slug="12345678-authentication",
        title="Authentication",
        summary="Old summary.",
        content_markdown="Old content.",
        created_at=created_at,
        updated_at=created_at,
    )

    updated_page = existing_page.update_from_compilation(
        slug="authentication",
        title="Authentication",
        summary="New summary.",
        content_markdown="New content.",
    )

    assert updated_page.id == page_id
    assert updated_page.owner_id == owner_id
    assert updated_page.document_id is None
    assert updated_page.slug == "authentication"
    assert updated_page.summary == "New summary."
    assert updated_page.created_at == created_at
