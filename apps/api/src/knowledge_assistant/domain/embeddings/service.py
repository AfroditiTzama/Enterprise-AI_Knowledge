from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    @abstractmethod
    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate an embedding vector for each document text."""
        raise NotImplementedError

    @abstractmethod
    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """Generate an embedding vector for a search query."""
        raise NotImplementedError