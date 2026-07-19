from knowledge_assistant.domain.documents.chunk_entities import (
    DocumentChunkEntity,
)
from knowledge_assistant.infrastructure.database.models.document_chunk import (
    DocumentChunkModel,
)


class DocumentChunkMapper:
    @staticmethod
    def to_domain(
        model: DocumentChunkModel,
    ) -> DocumentChunkEntity:
        return DocumentChunkEntity(
            id=model.id,
            document_id=model.document_id,
            chunk_index=model.chunk_index,
            text=model.text,
            page_number=model.page_number,
        )

    @staticmethod
    def to_model(
        entity: DocumentChunkEntity,
    ) -> DocumentChunkModel:
        return DocumentChunkModel(
            id=entity.id,
            document_id=entity.document_id,
            chunk_index=entity.chunk_index,
            text=entity.text,
            page_number=entity.page_number,
        )