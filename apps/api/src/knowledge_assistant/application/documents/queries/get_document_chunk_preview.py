from dataclasses import dataclass
from uuid import UUID

from knowledge_assistant.domain.documents.chunk_entities import (
    DocumentChunkEntity,
)
from knowledge_assistant.domain.documents.chunk_repository import (
    DocumentChunkRepository,
)
from knowledge_assistant.domain.documents.repository import (
    DocumentRepository,
)


@dataclass(frozen=True)
class DocumentChunkPreview:
    chunk_id: UUID
    document_id: UUID
    document_filename: str
    chunk_index: int
    page_number: int | None
    text: str


class GetDocumentChunkPreviewQuery:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        document_chunk_repository: DocumentChunkRepository,
    ) -> None:
        self._document_repository = (
            document_repository
        )
        self._document_chunk_repository = (
            document_chunk_repository
        )

    async def execute(
        self,
        *,
        chunk_id: UUID,
        owner_id: UUID,
    ) -> DocumentChunkPreview:
        chunk = (
            await self._document_chunk_repository
            .get_by_id(chunk_id)
        )

        if chunk is None:
            raise ValueError(
                "Document chunk was not found."
            )

        return await self._build_owned_preview(
            chunk=chunk,
            owner_id=owner_id,
        )

    async def execute_by_location(
        self,
        *,
        document_id: UUID,
        chunk_index: int,
        owner_id: UUID,
    ) -> DocumentChunkPreview:
        if chunk_index < 0:
            raise ValueError(
                "Document chunk was not found."
            )

        document = (
            await self._document_repository.get_by_id(
                document_id
            )
        )

        if (
            document is None
            or document.owner_id != owner_id
        ):
            raise ValueError(
                "Document chunk was not found."
            )

        chunks = (
            await self._document_chunk_repository
            .list_by_document_id(document_id)
        )

        chunk = next(
            (
                item
                for item in chunks
                if item.chunk_index == chunk_index
            ),
            None,
        )

        if chunk is None:
            raise ValueError(
                "Document chunk was not found."
            )

        return DocumentChunkPreview(
            chunk_id=chunk.id,
            document_id=document.id,
            document_filename=(
                document.original_filename
            ),
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            text=chunk.text,
        )

    async def _build_owned_preview(
        self,
        *,
        chunk: DocumentChunkEntity,
        owner_id: UUID,
    ) -> DocumentChunkPreview:
        document = (
            await self._document_repository.get_by_id(
                chunk.document_id
            )
        )

        if (
            document is None
            or document.owner_id != owner_id
        ):
            raise ValueError(
                "Document chunk was not found."
            )

        return DocumentChunkPreview(
            chunk_id=chunk.id,
            document_id=document.id,
            document_filename=(
                document.original_filename
            ),
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            text=chunk.text,
        )
