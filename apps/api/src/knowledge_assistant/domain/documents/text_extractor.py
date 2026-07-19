from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedTextSegment:
    text: str
    page_number: int | None = None


@dataclass(frozen=True)
class ExtractedDocument:
    segments: tuple[ExtractedTextSegment, ...]

    @property
    def full_text(self) -> str:
        return "\n\n".join(
            segment.text
            for segment in self.segments
            if segment.text.strip()
        )


class DocumentTextExtractor(ABC):
    @abstractmethod
    async def extract(
        self,
        *,
        file_content: bytes,
        original_filename: str,
        content_type: str | None,
    ) -> ExtractedDocument:
        """Extract structured text from a supported document."""
        raise NotImplementedError