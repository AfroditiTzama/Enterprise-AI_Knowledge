from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RetrievedKnowledgeSource:
    source_id: str
    source_type: str
    document_id: UUID
    title: str
    text: str
    score: float
    slug: str | None = None
    page_number: int | None = None
    chunk_index: int | None = None


@dataclass(frozen=True)
class GeneratedKnowledgeAnswer:
    answer_markdown: str
    used_source_ids: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeChatResult:
    answer_markdown: str
    retrieval_mode: str
    sources: tuple[RetrievedKnowledgeSource, ...]