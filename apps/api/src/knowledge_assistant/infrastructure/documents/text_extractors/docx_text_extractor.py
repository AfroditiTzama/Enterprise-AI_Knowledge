import asyncio
from io import BytesIO
from zipfile import BadZipFile

from docx import Document as OpenXmlDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from knowledge_assistant.domain.documents.text_extractor import (
    DocumentTextExtractor,
    ExtractedDocument,
    ExtractedTextSegment,
)


class DOCXTextExtractor(DocumentTextExtractor):
    async def extract(
        self,
        *,
        file_content: bytes,
        original_filename: str,
        content_type: str | None,
    ) -> ExtractedDocument:
        if not file_content:
            raise ValueError("DOCX file cannot be empty.")

        return await asyncio.to_thread(
            self._extract_sync,
            file_content,
        )

    @staticmethod
    def _extract_sync(
        file_content: bytes,
    ) -> ExtractedDocument:
        try:
            document = OpenXmlDocument(
                BytesIO(file_content)
            )
        except (PackageNotFoundError, BadZipFile, KeyError) as exc:
            raise ValueError(
                "The uploaded DOCX file is invalid or corrupted."
            ) from exc

        segments: list[ExtractedTextSegment] = []

        for block in document.iter_inner_content():
            if isinstance(block, Paragraph):
                paragraph_text = block.text.strip()

                if not paragraph_text:
                    continue

                segments.append(
                    ExtractedTextSegment(
                        text=paragraph_text,
                        page_number=None,
                    )
                )

            elif isinstance(block, Table):
                table_text = DOCXTextExtractor._extract_table_text(
                    block
                )

                if not table_text:
                    continue

                segments.append(
                    ExtractedTextSegment(
                        text=table_text,
                        page_number=None,
                    )
                )

        if not segments:
            raise ValueError(
                "No extractable text was found in the DOCX file."
            )

        return ExtractedDocument(
            segments=tuple(segments),
        )

    @staticmethod
    def _extract_table_text(table: Table) -> str:
        rows: list[str] = []

        for row in table.rows:
            cell_values = [
                cell.text.strip()
                for cell in row.cells
            ]

            if not any(cell_values):
                continue

            rows.append(" | ".join(cell_values))

        return "\n".join(rows)