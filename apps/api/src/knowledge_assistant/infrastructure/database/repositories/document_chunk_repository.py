from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_assistant.domain.documents.chunk_entities import (
    DocumentChunkEntity,
)
from knowledge_assistant.domain.documents.chunk_repository import (
    DocumentChunkRepository,
)
from knowledge_assistant.infrastructure.database.mappers.document_chunk_mapper import (
    DocumentChunkMapper,
)
from knowledge_assistant.infrastructure.database.models.document_chunk import (
    DocumentChunkModel,
)


class SQLAlchemyDocumentChunkRepository(DocumentChunkRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_for_document(
        self,
        *,
        document_id: UUID,
        chunks: tuple[DocumentChunkEntity, ...],
    ) -> None:
        delete_statement = delete(DocumentChunkModel).where(
            DocumentChunkModel.document_id == document_id
        )

        await self._session.execute(delete_statement)

        chunk_models = [
            DocumentChunkMapper.to_model(chunk)
            for chunk in chunks
        ]

        self._session.add_all(chunk_models)

        await self._session.flush()

    async def list_by_document_id(
        self,
        document_id: UUID,
    ) -> list[DocumentChunkEntity]:
        statement = (
            select(DocumentChunkModel)
            .where(
                DocumentChunkModel.document_id == document_id
            )
            .order_by(DocumentChunkModel.chunk_index.asc())
        )

        result = await self._session.execute(statement)
        chunk_models = result.scalars().all()

        return [
            DocumentChunkMapper.to_domain(chunk_model)
            for chunk_model in chunk_models
        ]