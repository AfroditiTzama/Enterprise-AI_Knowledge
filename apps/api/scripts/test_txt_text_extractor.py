import asyncio

from knowledge_assistant.infrastructure.documents.text_extractors.txt_text_extractor import (
    TXTTextExtractor,
)


async def main() -> None:
    test_text = (
        "Enterprise AI Knowledge Assistant\n\n"
        "Αυτό είναι ένα δοκιμαστικό ελληνικό αρχείο TXT.\n"
        "Το σύστημα πρέπει να εξαγάγει σωστά το περιεχόμενό του."
    )

    file_content = test_text.encode("utf-8")

    extractor = TXTTextExtractor()

    extracted_document = await extractor.extract(
        file_content=file_content,
        original_filename="test_document.txt",
        content_type="text/plain",
    )

    print(
        f"Extracted segments: "
        f"{len(extracted_document.segments)}"
    )

    print(
        f"Total characters: "
        f"{len(extracted_document.full_text)}"
    )

    print("\nExtracted content:")
    print("-" * 80)
    print(extracted_document.full_text)
    print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())