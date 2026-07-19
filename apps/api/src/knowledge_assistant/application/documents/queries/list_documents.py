from uuid import UUID

from knowledge_assistant.domain.documents.entities import Document
from knowledge_assistant.domain.documents.repository import DocumentRepository


class ListDocumentsQuery:
    def __init__(
        self,
        document_repository: DocumentRepository,
    ) -> None:
        self._document_repository = document_repository

    async def execute(
        self,
        *,
        owner_id: UUID,
    ) -> list[Document]:
        return await self._document_repository.list_by_owner_id(owner_id)