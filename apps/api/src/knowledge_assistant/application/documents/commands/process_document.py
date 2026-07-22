from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from knowledge_assistant.domain.documents.chunk_entities import (
    DocumentChunkEntity,
)
from knowledge_assistant.domain.documents.chunk_repository import (
    DocumentChunkRepository,
)
from knowledge_assistant.domain.documents.entities import Document
from knowledge_assistant.domain.documents.file_storage import FileStorage
from knowledge_assistant.domain.documents.repository import DocumentRepository
from knowledge_assistant.domain.documents.text_chunker import (
    DocumentChunk,
    DocumentTextChunker,
)
from knowledge_assistant.domain.documents.text_extractor import (
    DocumentTextExtractor,
    ExtractedDocument,
)
from knowledge_assistant.domain.embeddings.service import EmbeddingService
from knowledge_assistant.domain.jobs.entities import ProcessingJobStage
from knowledge_assistant.domain.vector_store.store import (
    VectorRecord,
    VectorStore,
)


ProgressCallback = Callable[
    [ProcessingJobStage, int],
    Awaitable[None],
]


@dataclass(frozen=True)
class ProcessDocumentResult:
    document: Document
    extracted_document: ExtractedDocument
    chunks: tuple[DocumentChunk, ...]


class ProcessDocumentCommand:
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_chunk_repository: DocumentChunkRepository,
        file_storage: FileStorage,
        text_extractor: DocumentTextExtractor,
        text_chunker: DocumentTextChunker,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ) -> None:
        self._document_repository = document_repository
        self._document_chunk_repository = document_chunk_repository
        self._file_storage = file_storage
        self._text_extractor = text_extractor
        self._text_chunker = text_chunker
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    async def execute(
        self,
        *,
        document_id: UUID,
        owner_id: UUID,
        progress_callback: ProgressCallback | None = None,
    ) -> ProcessDocumentResult:
        document = await self._document_repository.get_by_id(document_id)

        if document is None or document.owner_id != owner_id:
            raise ValueError("Document was not found.")

        document.mark_as_processing()
        document = await self._document_repository.update(document)

        try:
            await self._report(
                progress_callback,
                ProcessingJobStage.EXTRACTING,
                10,
            )
            file_content = await self._file_storage.read(
                document.storage_path
            )

            extracted_document = await self._text_extractor.extract(
                file_content=file_content,
                original_filename=document.original_filename,
                content_type=document.content_type,
            )

            await self._report(
                progress_callback,
                ProcessingJobStage.CHUNKING,
                40,
            )
            chunks = self._text_chunker.chunk(extracted_document)

            if not chunks:
                raise ValueError(
                    "No text chunks were created from the document."
                )

            chunk_entities = tuple(
                DocumentChunkEntity.create(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    page_number=chunk.page_number,
                )
                for chunk in chunks
            )

            await self._report(
                progress_callback,
                ProcessingJobStage.EMBEDDING,
                60,
            )
            embeddings = await self._embedding_service.embed_documents(
                [chunk.text for chunk in chunk_entities]
            )

            if len(embeddings) != len(chunk_entities):
                raise ValueError(
                    "Embedding count does not match chunk count."
                )

            await self._report(
                progress_callback,
                ProcessingJobStage.PERSISTING,
                85,
            )
            await self._document_chunk_repository.replace_for_document(
                document_id=document.id,
                chunks=chunk_entities,
            )

            vector_records = tuple(
                VectorRecord(
                    id=str(chunk_entity.id),
                    owner_id=document.owner_id,
                    document_id=document.id,
                    chunk_index=chunk_entity.chunk_index,
                    text=chunk_entity.text,
                    page_number=chunk_entity.page_number,
                    embedding=embedding,
                )
                for chunk_entity, embedding in zip(
                    chunk_entities,
                    embeddings,
                    strict=True,
                )
            )

            await self._vector_store.replace_document_records(
                owner_id=document.owner_id,
                document_id=document.id,
                records=vector_records,
            )

            document.mark_as_processed()
            document = await self._document_repository.update(document)

            return ProcessDocumentResult(
                document=document,
                extracted_document=extracted_document,
                chunks=chunks,
            )

        except Exception:
            document.mark_as_failed()
            await self._document_repository.update(document)
            raise

    @staticmethod
    async def _report(
        callback: ProgressCallback | None,
        stage: ProcessingJobStage,
        progress: int,
    ) -> None:
        if callback is not None:
            await callback(stage, progress)
