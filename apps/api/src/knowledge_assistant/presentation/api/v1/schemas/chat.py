from uuid import UUID

from pydantic import BaseModel, Field


class AskKnowledgeRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=4000,
    )


class KnowledgeSourceResponse(BaseModel):
    source_id: str
    source_type: str
    document_id: UUID
    title: str
    score: float
    slug: str | None = None
    page_number: int | None = None
    chunk_index: int | None = None


class AskKnowledgeResponse(BaseModel):
    answer_markdown: str
    retrieval_mode: str
    sources: list[KnowledgeSourceResponse]