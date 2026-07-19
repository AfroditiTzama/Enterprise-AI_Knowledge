from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from knowledge_assistant.domain.documents.chunk_entities import (
    DocumentChunkEntity,
)


@dataclass(frozen=True)
class WikiPageDraft:
    title: str
    slug: str
    summary: str
    content_markdown: str
    source_chunk_ids: tuple[UUID, ...]
    related_page_slugs: tuple[str, ...]


@dataclass(frozen=True)
class WikiCompilation:
    pages: tuple[WikiPageDraft, ...]


class WikiCompiler(ABC):
    @abstractmethod
    async def compile(
        self,
        *,
        document_title: str,
        chunks: tuple[DocumentChunkEntity, ...],
    ) -> WikiCompilation:
        """Compile document chunks into structured wiki pages."""
        raise NotImplementedError