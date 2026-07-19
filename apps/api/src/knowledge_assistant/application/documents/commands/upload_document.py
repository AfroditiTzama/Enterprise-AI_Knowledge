from uuid import UUID

from knowledge_assistant.domain.documents.entities import Document
from knowledge_assistant.domain.documents.file_storage import FileStorage
from knowledge_assistant.domain.documents.repository import DocumentRepository


class UploadDocumentCommand:
    def __init__(
        self,
        document_repository: DocumentRepository,
        file_storage: FileStorage,
    ) -> None:
        self._document_repository = document_repository
        self._file_storage = file_storage

    async def execute(
        self,
        *,
        owner_id: UUID,
        original_filename: str,
        content_type: str | None,
        file_content: bytes,
    ) -> Document:
        if not original_filename.strip():
            raise ValueError("Original filename cannot be empty.")

        if not file_content:
            raise ValueError("Uploaded file cannot be empty.")

        stored_file = await self._file_storage.save(
            file_content=file_content,
            original_filename=original_filename,
        )

        document = Document.create(
            owner_id=owner_id,
            original_filename=original_filename,
            stored_filename=stored_file.stored_filename,
            storage_path=stored_file.storage_path,
            content_type=content_type,
            size_bytes=stored_file.size_bytes,
        )

        try:
            saved_document = await self._document_repository.add(document)
        except Exception:
            await self._file_storage.delete(stored_file.storage_path)
            raise

        return saved_document