from abc import ABC, abstractmethod
from dataclasses import dataclass

from knowledge_assistant.domain.documents.text_extractor import (
    ExtractedDocument,
)


@dataclass(frozen=True)
class DocumentChunk:
    index: int
    text: str
    page_number: int | None


class DocumentTextChunker(ABC):
    @abstractmethod
    def chunk(
        self,
        extracted_document: ExtractedDocument,
    ) -> tuple[DocumentChunk, ...]:
        """Split an extracted document into smaller text chunks."""
        raise NotImplementedError