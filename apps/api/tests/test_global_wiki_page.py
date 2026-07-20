from uuid import uuid4

from knowledge_assistant.domain.wiki.entities import (
    WikiPage,
)


def test_wiki_page_can_exist_without_primary_document() -> None:
    page = WikiPage.create(
        owner_id=uuid4(),
        document_id=None,
        slug="authentication",
        title="Authentication",
        summary="Authentication knowledge.",
        content_markdown=(
            "Authentication details from multiple sources."
        ),
    )

    assert page.document_id is None
    assert page.slug == "authentication"
