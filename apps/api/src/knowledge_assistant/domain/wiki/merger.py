from abc import ABC, abstractmethod
from dataclasses import dataclass

from knowledge_assistant.domain.wiki.compiler import WikiPageDraft
from knowledge_assistant.domain.wiki.entities import WikiPage


@dataclass(frozen=True)
class WikiConflictDraft:
    existing_statement: str
    incoming_statement: str
    explanation: str


@dataclass(frozen=True)
class WikiMergeResult:
    title: str
    summary: str
    content_markdown: str
    conflicts: tuple[WikiConflictDraft, ...]


class WikiPageMerger(ABC):
    @abstractmethod
    async def merge(
        self,
        *,
        existing_page: WikiPage,
        incoming_draft: WikiPageDraft,
        document_title: str,
    ) -> WikiMergeResult:
        """Merge new sourced knowledge into an existing Wiki page."""
        raise NotImplementedError
