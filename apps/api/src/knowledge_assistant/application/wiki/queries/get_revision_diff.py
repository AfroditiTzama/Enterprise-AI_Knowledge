from dataclasses import dataclass
from difflib import ndiff
from uuid import UUID

from knowledge_assistant.domain.wiki.repository import WikiRepository


@dataclass(frozen=True)
class WikiRevisionDiffLine:
    kind: str
    text: str


@dataclass(frozen=True)
class WikiRevisionDiffResult:
    from_revision_number: int | None
    to_revision_number: int
    lines: tuple[WikiRevisionDiffLine, ...]


class GetWikiRevisionDiffQuery:
    def __init__(self, repository: WikiRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        owner_id: UUID,
        slug: str,
        revision_number: int,
    ) -> WikiRevisionDiffResult:
        revisions = await self._repository.list_revisions_by_slug(
            owner_id=owner_id,
            slug=slug,
        )
        revisions_by_number = {
            revision.revision_number: revision
            for revision in revisions
        }
        target = revisions_by_number.get(revision_number)

        if target is None:
            raise ValueError("Wiki revision was not found.")

        previous = revisions_by_number.get(revision_number - 1)
        previous_lines = (
            previous.content_markdown.splitlines()
            if previous is not None
            else []
        )
        target_lines = target.content_markdown.splitlines()

        lines: list[WikiRevisionDiffLine] = []
        for line in ndiff(previous_lines, target_lines):
            prefix = line[:2]
            if prefix == "? ":
                continue

            kind = {
                "+ ": "added",
                "- ": "removed",
                "  ": "context",
            }.get(prefix, "context")
            lines.append(
                WikiRevisionDiffLine(
                    kind=kind,
                    text=line[2:],
                )
            )

        return WikiRevisionDiffResult(
            from_revision_number=(
                previous.revision_number
                if previous is not None
                else None
            ),
            to_revision_number=target.revision_number,
            lines=tuple(lines),
        )
