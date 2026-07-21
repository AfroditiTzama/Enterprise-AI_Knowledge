from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from knowledge_assistant.application.documents.commands.delete_document import (
    DeleteDocumentCommand,
)
from knowledge_assistant.domain.documents.entities import (
    Document,
    DocumentStatus,
)


class FakeDocumentRepository:
    def __init__(self, document: Document | None) -> None:
        self.document = document
        self.deleted_ids: list[UUID] = []

    async def get_by_id(self, document_id: UUID) -> Document | None:
        if self.document is None or self.document.id != document_id:
            return None
        return self.document

    async def delete(self, document_id: UUID) -> None:
        self.deleted_ids.append(document_id)


class FakeFileStorage:
    def __init__(self) -> None:
        self.deleted_paths: list[str] = []

    async def delete(self, storage_path: str) -> None:
        self.deleted_paths.append(storage_path)


class FakeVectorStore:
    def __init__(self) -> None:
        self.deleted_documents: list[tuple[UUID, UUID]] = []

    async def delete_document_records(
        self,
        *,
        owner_id: UUID,
        document_id: UUID,
    ) -> None:
        self.deleted_documents.append((owner_id, document_id))


def create_document(owner_id: UUID) -> Document:
    now = datetime.now(timezone.utc)
    return Document(
        id=uuid4(),
        owner_id=owner_id,
        original_filename="knowledge.pdf",
        stored_filename="stored.pdf",
        storage_path="stored.pdf",
        content_type="application/pdf",
        size_bytes=100,
        status=DocumentStatus.PROCESSED,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_delete_document_removes_all_owned_resources() -> None:
    owner_id = uuid4()
    document = create_document(owner_id)
    repository = FakeDocumentRepository(document)
    storage = FakeFileStorage()
    vector_store = FakeVectorStore()
    command = DeleteDocumentCommand(
        document_repository=repository,
        file_storage=storage,
        vector_store=vector_store,
    )

    await command.execute(
        document_id=document.id,
        owner_id=owner_id,
    )

    assert repository.deleted_ids == [document.id]
    assert storage.deleted_paths == [document.storage_path]
    assert vector_store.deleted_documents == [
        (owner_id, document.id)
    ]


@pytest.mark.asyncio
async def test_delete_document_rejects_different_owner() -> None:
    owner_id = uuid4()
    document = create_document(owner_id)
    repository = FakeDocumentRepository(document)
    storage = FakeFileStorage()
    vector_store = FakeVectorStore()
    command = DeleteDocumentCommand(
        document_repository=repository,
        file_storage=storage,
        vector_store=vector_store,
    )

    with pytest.raises(ValueError, match="Document was not found"):
        await command.execute(
            document_id=document.id,
            owner_id=uuid4(),
        )

    assert repository.deleted_ids == []
    assert storage.deleted_paths == []
    assert vector_store.deleted_documents == []
