from knowledge_assistant.domain.documents.text_extractor import (
    ExtractedDocument,
    ExtractedTextSegment,
)
from knowledge_assistant.infrastructure.documents.chunkers.recursive_text_chunker import (
    RecursiveTextChunker,
)


def main() -> None:
    extracted_document = ExtractedDocument(
        segments=(
            ExtractedTextSegment(
                text=(
                    "This is the first paragraph of the document. "
                    "It contains enough text to create multiple chunks.\n\n"
                    "This is the second paragraph. "
                    "The chunker should preserve part of the previous chunk "
                    "as overlap when creating the next one."
                ),
                page_number=1,
            ),
            ExtractedTextSegment(
                text=(
                    "This text belongs to the second page. "
                    "Its chunks must keep page number two."
                ),
                page_number=2,
            ),
        )
    )

    chunker = RecursiveTextChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = chunker.chunk(extracted_document)

    print(f"Total chunks: {len(chunks)}")

    for chunk in chunks:
        print("-" * 80)
        print(f"Index: {chunk.index}")
        print(f"Page: {chunk.page_number}")
        print(f"Characters: {len(chunk.text)}")
        print(chunk.text)

        assert len(chunk.text) <= 100
        assert chunk.text.strip()
        assert chunk.page_number in (1, 2)

    assert [chunk.index for chunk in chunks] == list(
        range(len(chunks))
    )

    print("\nChunking test completed successfully.")


if __name__ == "__main__":
    main()