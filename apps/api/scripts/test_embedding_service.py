import asyncio
import math

from knowledge_assistant.infrastructure.embeddings.sentence_transformer_service import (
    SentenceTransformerEmbeddingService,
)


async def main() -> None:
    service = SentenceTransformerEmbeddingService()

    texts = [
        "Η τεχνητή νοημοσύνη χρησιμοποιείται για ανάλυση εγγράφων.",
        "Artificial intelligence can analyze enterprise documents.",
        "Σήμερα ο καιρός είναι ηλιόλουστος.",
    ]

    document_embeddings = await service.embed_documents(texts)

    query_embedding = await service.embed_query(
        "Πώς χρησιμοποιείται η τεχνητή νοημοσύνη στα έγγραφα;"
    )

    print(f"Document embeddings: {len(document_embeddings)}")
    print(f"Embedding dimension: {len(document_embeddings[0])}")
    print(f"Query dimension: {len(query_embedding)}")

    for index, embedding in enumerate(document_embeddings):
        vector_norm = math.sqrt(
            sum(value * value for value in embedding)
        )

        print(
            f"Embedding {index}: "
            f"dimension={len(embedding)}, "
            f"norm={vector_norm:.4f}"
        )

    assert len(document_embeddings) == len(texts)
    assert len(query_embedding) == len(document_embeddings[0])
    assert all(
        len(embedding) == len(query_embedding)
        for embedding in document_embeddings
    )

    print("Embedding service test completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())