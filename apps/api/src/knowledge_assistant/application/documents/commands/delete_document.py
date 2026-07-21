from uuid import UUID

from knowledge_assistant.domain.documents.file_storage import FileStorage
from knowledge_assistant.domain.documents.repository import DocumentRepository
from knowledge_assistant.domain.vector_store.store import VectorStore


class DeleteDocumentCommand:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        file_storage: FileStorage,
        vector_store: VectorStore,
    ) -> None:
        self._document_repository = document_repository
        self._file_storage = file_storage
        self._vector_store = vector_store

    async def execute(
        self,
        *,
        document_id: UUID,
        owner_id: UUID,
    ) -> None:
        document = await self._document_repository.get_by_id(
            document_id
        )

        if document is None or document.owner_id != owner_id:
            raise ValueError("Document was not found.")

        await self._vector_store.delete_document_records(
            owner_id=owner_id,
            document_id=document_id,
        )

        await self._file_storage.delete(document.storage_path)
        await self._document_repository.delete(document_id)
