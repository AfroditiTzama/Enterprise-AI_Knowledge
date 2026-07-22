from datetime import datetime, timezone
from uuid import uuid4

from knowledge_assistant.application.wiki.services.maintenance import (
    detect_maintenance_suggestions,
)
from knowledge_assistant.domain.wiki.entities import (
    WikiMaintenanceIssueType,
    WikiPage,
    WikiPageDetails,
)


def _page(title: str, slug: str, content: str) -> WikiPageDetails:
    now = datetime.now(timezone.utc)
    return WikiPageDetails(
        page=WikiPage(
            id=uuid4(),
            owner_id=uuid4(),
            document_id=None,
            slug=slug,
            title=title,
            summary="Transformer model for molecular generation",
            content_markdown=content,
            created_at=now,
            updated_at=now,
        ),
        sources=(),
        related_pages=(),
        backlinks=(),
    )


def test_maintenance_detects_orphans_and_duplicates() -> None:
    first = _page(
        "Molecular Transformer",
        "molecular-transformer",
        "A small factual paragraph about molecular transformer models.",
    )
    second = _page(
        "Molecular Transformer Model",
        "molecular-transformer-model",
        "Another small factual paragraph about molecular transformer models.",
    )

    suggestions = detect_maintenance_suggestions([first, second])
    issue_types = {suggestion.issue_type for suggestion in suggestions}

    assert WikiMaintenanceIssueType.ORPHAN in issue_types
    assert WikiMaintenanceIssueType.DUPLICATE in issue_types
    assert WikiMaintenanceIssueType.UNDERSIZED in issue_types
