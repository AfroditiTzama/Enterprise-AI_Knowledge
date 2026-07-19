from pathlib import Path

from knowledge_assistant.domain.documents.text_extractor import (
    DocumentTextExtractor,
    ExtractedDocument,
)
from knowledge_assistant.infrastructure.documents.text_extractors.docx_text_extractor import (
    DOCXTextExtractor,
)
from knowledge_assistant.infrastructure.documents.text_extractors.pdf_text_extractor import (
    PDFTextExtractor,
)
from knowledge_assistant.infrastructure.documents.text_extractors.txt_text_extractor import (
    TXTTextExtractor,
)


class CompositeDocumentTextExtractor(DocumentTextExtractor):
    def __init__(self) -> None:
        self._extractors_by_extension: dict[
            str,
            DocumentTextExtractor,
        ] = {
            ".pdf": PDFTextExtractor(),
            ".docx": DOCXTextExtractor(),
            ".txt": TXTTextExtractor(),
        }

        self._extractors_by_content_type: dict[
            str,
            DocumentTextExtractor,
        ] = {
            "application/pdf": PDFTextExtractor(),
            (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ): DOCXTextExtractor(),
            "text/plain": TXTTextExtractor(),
        }

    async def extract(
        self,
        *,
        file_content: bytes,
        original_filename: str,
        content_type: str | None,
    ) -> ExtractedDocument:
        extractor = self._select_extractor(
            original_filename=original_filename,
            content_type=content_type,
        )

        return await extractor.extract(
            file_content=file_content,
            original_filename=original_filename,
            content_type=content_type,
        )

    def _select_extractor(
        self,
        *,
        original_filename: str,
        content_type: str | None,
    ) -> DocumentTextExtractor:
        extension = Path(original_filename).suffix.lower()

        extractor = self._extractors_by_extension.get(extension)

        if extractor is not None:
            return extractor

        normalized_content_type = (
            content_type.split(";", maxsplit=1)[0]
            .strip()
            .lower()
            if content_type
            else ""
        )

        extractor = self._extractors_by_content_type.get(
            normalized_content_type
        )

        if extractor is not None:
            return extractor

        raise ValueError(
            "Unsupported document type. "
            "Supported file types are PDF, DOCX and TXT."
        )