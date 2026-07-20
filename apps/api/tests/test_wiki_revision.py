from uuid import uuid4

import pytest

from knowledge_assistant.domain.wiki.entities import (
    WikiPageRevision,
    WikiRevisionOperation,
)


def test_wiki_revision_creation() -> None:
    owner_id = uuid4()
    document_id = uuid4()
    page_id = uuid4()

    revision = WikiPageRevision.create(
        wiki_page_id=page_id,
        owner_id=owner_id,
        page_slug="  Authentication Flow  ",
        revision_number=1,
        title=" Authentication ",
        summary=" Login process ",
        content_markdown="JWT authentication details.",
        operation=WikiRevisionOperation.CREATE,
        triggering_document_id=document_id,
    )

    assert revision.page_slug == "authentication flow"
    assert revision.title == "Authentication"
    assert revision.summary == "Login process"
    assert revision.revision_number == 1
    assert (
        revision.operation
        == WikiRevisionOperation.CREATE
    )


def test_wiki_revision_rejects_invalid_number() -> None:
    with pytest.raises(
        ValueError,
        match="revision number must be positive",
    ):
        WikiPageRevision.create(
            wiki_page_id=uuid4(),
            owner_id=uuid4(),
            page_slug="authentication",
            revision_number=0,
            title="Authentication",
            summary="Summary",
            content_markdown="Content",
            operation=WikiRevisionOperation.CREATE,
            triggering_document_id=uuid4(),
        )
