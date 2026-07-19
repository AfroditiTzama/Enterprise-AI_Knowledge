import asyncio
from pathlib import Path

from knowledge_assistant.infrastructure.documents.text_extractors.pdf_text_extractor import (
    PDFTextExtractor,
)


PDF_PATH = Path(
    "storage/documents/de54408d24c9433694d59aacae1f60bc.pdf"
)


async def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"PDF file was not found: {PDF_PATH}"
        )

    file_content = PDF_PATH.read_bytes()

    extractor = PDFTextExtractor()

    extracted_document = await extractor.extract(
        file_content=file_content,
        original_filename="5_AI_PROVIDERS.pdf",
        content_type="application/pdf",
    )

    print(f"Extracted pages: {len(extracted_document.segments)}")
    print(f"Total characters: {len(extracted_document.full_text)}")

    first_segment = extracted_document.segments[0]

    print(f"First extracted page: {first_segment.page_number}")
    print("\nText preview:")
    print("-" * 80)
    print(first_segment.text[:1000])
    print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())