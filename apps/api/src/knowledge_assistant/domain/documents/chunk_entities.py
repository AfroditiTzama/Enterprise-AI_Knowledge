from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class DocumentChunkEntity:
    id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    page_number: int | None

    @classmethod
    def create(
        cls,
        *,
        document_id: UUID,
        chunk_index: int,
        text: str,
        page_number: int | None,
    ) -> "DocumentChunkEntity":
        if chunk_index < 0:
            raise ValueError("Chunk index cannot be negative.")

        if not text.strip():
            raise ValueError("Chunk text cannot be empty.")

        return cls(
            id=uuid4(),
            document_id=document_id,
            chunk_index=chunk_index,
            text=text.strip(),
            page_number=page_number,
        )