import asyncio
from pathlib import Path
from typing import Any
from uuid import UUID

import chromadb

from knowledge_assistant.domain.vector_store.store import (
    VectorRecord,
    VectorSearchResult,
    VectorStore,
)


class ChromaVectorStore(VectorStore):
    def __init__(
        self,
        *,
        storage_directory: str | Path = "storage/chroma",
        collection_name: str = "document_chunks",
    ) -> None:
        self._client = chromadb.PersistentClient(
            path=str(Path(storage_directory).resolve())
        )

        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
            configuration={
                "hnsw": {
                    "space": "cosine",
                }
            },
        )

    async def replace_document_records(
        self,
        *,
        owner_id: UUID,
        document_id: UUID,
        records: tuple[VectorRecord, ...],
    ) -> None:
        await asyncio.to_thread(
            self._replace_document_records_sync,
            owner_id,
            document_id,
            records,
        )

    async def search(
        self,
        *,
        owner_id: UUID,
        query_embedding: list[float],
        limit: int = 5,
    ) -> tuple[VectorSearchResult, ...]:
        if not query_embedding:
            raise ValueError("Query embedding cannot be empty.")

        if limit <= 0:
            raise ValueError("Search limit must be greater than zero.")

        return await asyncio.to_thread(
            self._search_sync,
            owner_id,
            query_embedding,
            limit,
        )

    def _replace_document_records_sync(
        self,
        owner_id: UUID,
        document_id: UUID,
        records: tuple[VectorRecord, ...],
    ) -> None:
        self._collection.delete(
            where={
                "$and": [
                    {"owner_id": str(owner_id)},
                    {"document_id": str(document_id)},
                ]
            }
        )

        if not records:
            return

        ids: list[str] = []
        embeddings: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, str | int]] = []

        for record in records:
            if record.owner_id != owner_id:
                raise ValueError("Vector record owner does not match.")

            if record.document_id != document_id:
                raise ValueError("Vector record document does not match.")

            metadata: dict[str, str | int] = {
                "owner_id": str(record.owner_id),
                "document_id": str(record.document_id),
                "chunk_index": record.chunk_index,
            }

            if record.page_number is not None:
                metadata["page_number"] = record.page_number

            ids.append(record.id)
            embeddings.append(record.embedding)
            documents.append(record.text)
            metadatas.append(metadata)

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def _search_sync(
        self,
        owner_id: UUID,
        query_embedding: list[float],
        limit: int,
    ) -> tuple[VectorSearchResult, ...]:
        result: dict[str, Any] = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"owner_id": str(owner_id)},
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        search_results: list[VectorSearchResult] = []

        for record_id, document, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=True,
        ):
            if document is None or metadata is None:
                continue

            page_number = metadata.get("page_number")

            search_results.append(
                VectorSearchResult(
                    id=record_id,
                    document_id=UUID(metadata["document_id"]),
                    chunk_index=int(metadata["chunk_index"]),
                    text=document,
                    page_number=(
                        int(page_number)
                        if page_number is not None
                        else None
                    ),
                    score=1.0 - float(distance),
                )
            )

        return tuple(search_results)