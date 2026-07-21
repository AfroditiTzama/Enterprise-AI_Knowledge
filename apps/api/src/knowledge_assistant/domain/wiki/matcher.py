from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from knowledge_assistant.domain.wiki.compiler import (
    WikiPageDraft,
)
from knowledge_assistant.domain.wiki.entities import (
    WikiPage,
)


class WikiMatchDecision(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    SEMANTIC_CANDIDATE = "SEMANTIC_CANDIDATE"
    CREATE = "CREATE"


@dataclass(frozen=True)
class WikiMatchResult:
    draft_slug: str
    decision: WikiMatchDecision
    matched_page_id: UUID | None
    matched_page_slug: str | None
    score: float | None


class WikiSemanticMatcher(ABC):
    @abstractmethod
    async def match(
        self,
        *,
        drafts: tuple[WikiPageDraft, ...],
        existing_pages: tuple[WikiPage, ...],
    ) -> tuple[WikiMatchResult, ...]:
        """Find exact and semantic matches for Wiki drafts."""
        raise NotImplementedError
