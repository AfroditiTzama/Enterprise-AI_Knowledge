import pytest

from knowledge_assistant.core.config import Settings
from knowledge_assistant.domain.documents.text_extractor import (
    ExtractedDocument,
    ExtractedTextSegment,
)
from knowledge_assistant.infrastructure.documents.chunkers.recursive_text_chunker import (
    RecursiveTextChunker,
)
from knowledge_assistant.infrastructure.documents.file_validator import (
    DocumentFileValidator,
)


def test_section_metadata_is_preserved_in_child_chunks() -> None:
    extracted = ExtractedDocument(
        segments=(
            ExtractedTextSegment(
                text="Methods",
                page_number=2,
                section_title="Methods",
                section_path=("Methods",),
                content_type="heading",
                heading_level=1,
                extraction_method="layout",
            ),
            ExtractedTextSegment(
                text="A sufficiently long methods paragraph for retrieval.",
                page_number=2,
                section_title="Methods",
                section_path=("Methods",),
                content_type="text",
                extraction_method="layout",
            ),
        )
    )

    chunks = RecursiveTextChunker(chunk_size=80, chunk_overlap=10).chunk(
        extracted
    )

    assert len(chunks) == 1
    assert chunks[0].text.startswith("Section: Methods")
    assert chunks[0].section_title == "Methods"
    assert chunks[0].page_number == 2


@pytest.mark.asyncio
async def test_file_validator_rejects_mismatched_pdf_signature() -> None:
    validator = DocumentFileValidator(Settings())

    with pytest.raises(ValueError, match="valid PDF"):
        await validator.validate(
            original_filename="report.pdf",
            content_type="application/pdf",
            file_content=b"not a pdf",
        )


@pytest.mark.asyncio
async def test_file_validator_rejects_active_pdf_content() -> None:
    validator = DocumentFileValidator(Settings())

    with pytest.raises(ValueError, match="active or embedded"):
        await validator.validate(
            original_filename="report.pdf",
            content_type="application/pdf",
            file_content=b"%PDF-1.7\n/JavaScript\n%%EOF",
        )
