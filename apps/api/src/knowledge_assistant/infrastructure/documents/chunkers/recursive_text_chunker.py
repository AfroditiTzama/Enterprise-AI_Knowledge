from knowledge_assistant.domain.documents.text_chunker import (
    DocumentChunk,
    DocumentTextChunker,
)
from knowledge_assistant.domain.documents.text_extractor import (
    ExtractedDocument,
)


class RecursiveTextChunker(DocumentTextChunker):
    def __init__(
        self,
        *,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("Chunk size must be greater than zero.")

        if chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative.")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "Chunk overlap must be smaller than chunk size."
            )

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = (
            "\n\n",
            "\n",
            ". ",
            " ",
        )

    def chunk(
        self,
        extracted_document: ExtractedDocument,
    ) -> tuple[DocumentChunk, ...]:
        chunks: list[DocumentChunk] = []
        chunk_index = 0

        for segment in extracted_document.segments:
            text = segment.text.strip()

            if not text:
                continue

            for chunk_text in self._split_text(text):
                chunks.append(
                    DocumentChunk(
                        index=chunk_index,
                        text=chunk_text,
                        page_number=segment.page_number,
                    )
                )
                chunk_index += 1

        return tuple(chunks)

    def _split_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            maximum_end = min(
                start + self._chunk_size,
                text_length,
            )

            end = maximum_end

            if maximum_end < text_length:
                preferred_end = self._find_split_position(
                    text=text,
                    start=start,
                    maximum_end=maximum_end,
                )

                if preferred_end > start:
                    end = preferred_end

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(chunk_text)

            if end >= text_length:
                break

            next_start = end - self._chunk_overlap

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    def _find_split_position(
        self,
        *,
        text: str,
        start: int,
        maximum_end: int,
    ) -> int:
        minimum_split_position = start + (self._chunk_size // 2)
        search_area = text[start:maximum_end]

        for separator in self._separators:
            relative_position = search_area.rfind(separator)

            if relative_position == -1:
                continue

            split_position = (
                start
                + relative_position
                + len(separator)
            )

            if split_position >= minimum_split_position:
                return split_position

        return maximum_end