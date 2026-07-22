from uuid import uuid4

from knowledge_assistant.domain.wiki.entities import (
    WikiConflictStatus,
    WikiPageConflict,
)


def test_wiki_conflict_is_open_by_default() -> None:
    conflict = WikiPageConflict.create(
        owner_id=uuid4(),
        wiki_page_id=uuid4(),
        source_document_id=uuid4(),
        existing_statement="The model uses 12 layers.",
        incoming_statement="The model uses 24 layers.",
        explanation="The sources report different layer counts.",
    )

    assert conflict.status == WikiConflictStatus.OPEN
    assert conflict.resolved_at is None
    assert conflict.resolution_note == ""
