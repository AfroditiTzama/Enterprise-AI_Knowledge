from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from knowledge_assistant.domain.documents.entities import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    original_filename: str
    content_type: str | None
    size_bytes: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

class ProcessDocumentResponse(BaseModel):
    document: DocumentResponse
    extracted_segments: int
    extracted_characters: int
    chunks_count: int
    text_preview: str