from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from knowledge_assistant.application.wiki.queries.get_revision_diff import (
    GetWikiRevisionDiffQuery,
)
from knowledge_assistant.domain.wiki.entities import (
    WikiPageRevision,
    WikiRevisionOperation,
)


class FakeWikiRepository:
    def __init__(
        self,
        revisions: list[WikiPageRevision],
    ) -> None:
        self.revisions = revisions

    async def list_revisions_by_slug(
        self,
        *,
        owner_id: UUID,
        slug: str,
    ) -> list[WikiPageRevision]:
        del owner_id, slug
        return self.revisions


def create_revision(
    number: int,
    content: str,
) -> WikiPageRevision:
    return WikiPageRevision(
        id=uuid4(),
        wiki_page_id=uuid4(),
        owner_id=uuid4(),
        page_slug="authentication",
        revision_number=number,
        title="Authentication",
        summary="Authentication summary.",
        content_markdown=content,
        operation=WikiRevisionOperation.UPDATE,
        triggering_document_id=uuid4(),
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_revision_diff_marks_added_and_removed_lines() -> None:
    repository = FakeWikiRepository(
        [
            create_revision(2, "First line\nNew line"),
            create_revision(1, "First line\nOld line"),
        ]
    )
    query = GetWikiRevisionDiffQuery(repository)  # type: ignore[arg-type]

    result = await query.execute(
        owner_id=uuid4(),
        slug="authentication",
        revision_number=2,
    )

    kinds = [line.kind for line in result.lines]
    texts = [line.text for line in result.lines]

    assert "removed" in kinds
    assert "added" in kinds
    assert "Old line" in texts
    assert "New line" in texts
