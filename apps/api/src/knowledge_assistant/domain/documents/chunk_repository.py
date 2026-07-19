from abc import ABC, abstractmethod
from uuid import UUID

from knowledge_assistant.domain.documents.chunk_entities import (
    DocumentChunkEntity,
)


class DocumentChunkRepository(ABC):
    @abstractmethod
    async def replace_for_document(
        self,
        *,
        document_id: UUID,
        chunks: tuple[DocumentChunkEntity, ...],
    ) -> None:
        """Replace all existing chunks of a document."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_document_id(
        self,
        document_id: UUID,
    ) -> list[DocumentChunkEntity]:
        """Return all chunks belonging to a document."""
        raise NotImplementedError