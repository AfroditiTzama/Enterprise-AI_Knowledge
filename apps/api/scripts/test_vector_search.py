import argparse
import asyncio
from uuid import UUID

from knowledge_assistant.infrastructure.embeddings.sentence_transformer_service import (
    SentenceTransformerEmbeddingService,
)
from knowledge_assistant.infrastructure.vector_store.chroma_store import (
    ChromaVectorStore,
)


async def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "owner_id",
        type=UUID,
        help="Authenticated user's UUID",
    )
    parser.add_argument(
        "query",
        type=str,
        help="Semantic search question",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    embedding_service = SentenceTransformerEmbeddingService()

    vector_store = ChromaVectorStore(
        storage_directory="storage/chroma",
        collection_name="document_chunks",
    )

    query_embedding = await embedding_service.embed_query(
        args.query
    )

    results = await vector_store.search(
        owner_id=args.owner_id,
        query_embedding=query_embedding,
        limit=args.limit,
    )

    print(f"Results found: {len(results)}")

    for index, result in enumerate(results, start=1):
        print("\n" + "=" * 80)
        print(f"Result: {index}")
        print(f"Document ID: {result.document_id}")
        print(f"Chunk index: {result.chunk_index}")
        print(f"Page: {result.page_number}")
        print(f"Similarity score: {result.score:.4f}")
        print("-" * 80)
        print(result.text[:700])


if __name__ == "__main__":
    asyncio.run(main())