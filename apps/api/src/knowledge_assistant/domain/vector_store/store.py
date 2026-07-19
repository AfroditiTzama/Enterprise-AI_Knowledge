from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VectorRecord:
    id: str
    owner_id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    page_number: int | None
    embedding: list[float]


@dataclass(frozen=True)
class VectorSearchResult:
    id: str
    document_id: UUID
    chunk_index: int
    text: str
    page_number: int | None
    score: float


class VectorStore(ABC):
    @abstractmethod
    async def replace_document_records(
        self,
        *,
        owner_id: UUID,
        document_id: UUID,
        records: tuple[VectorRecord, ...],
    ) -> None:
        """Replace all vector records belonging to one document."""
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        *,
        owner_id: UUID,
        query_embedding: list[float],
        limit: int = 5,
    ) -> tuple[VectorSearchResult, ...]:
        """Search only inside documents owned by the user."""
        raise NotImplementedError