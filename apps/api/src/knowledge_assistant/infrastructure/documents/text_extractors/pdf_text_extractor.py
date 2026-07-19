import asyncio
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from knowledge_assistant.domain.documents.text_extractor import (
    DocumentTextExtractor,
    ExtractedDocument,
    ExtractedTextSegment,
)


class PDFTextExtractor(DocumentTextExtractor):
    async def extract(
        self,
        *,
        file_content: bytes,
        original_filename: str,
        content_type: str | None,
    ) -> ExtractedDocument:
        if not file_content:
            raise ValueError("PDF file cannot be empty.")

        return await asyncio.to_thread(
            self._extract_sync,
            file_content,
        )

    @staticmethod
    def _extract_sync(
        file_content: bytes,
    ) -> ExtractedDocument:
        try:
            reader = PdfReader(
                BytesIO(file_content),
                strict=False,
            )
        except PdfReadError as exc:
            raise ValueError(
                "The uploaded PDF is invalid or corrupted."
            ) from exc

        if reader.is_encrypted:
            raise ValueError(
                "Password-protected PDF files are not supported."
            )

        segments: list[ExtractedTextSegment] = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            page_text = page.extract_text() or ""
            page_text = page_text.strip()

            if not page_text:
                continue

            segments.append(
                ExtractedTextSegment(
                    text=page_text,
                    page_number=page_number,
                )
            )

        if not segments:
            raise ValueError(
                "No extractable text was found in the PDF."
            )

        return ExtractedDocument(
            segments=tuple(segments),
        )