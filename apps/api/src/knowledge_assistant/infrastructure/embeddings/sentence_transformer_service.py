import asyncio

from sentence_transformers import SentenceTransformer

from knowledge_assistant.domain.embeddings.service import (
    EmbeddingService,
)


class SentenceTransformerEmbeddingService(EmbeddingService):
    def __init__(
        self,
        model_name: str = (
            "sentence-transformers/"
            "paraphrase-multilingual-MiniLM-L12-v2"
        ),
    ) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        cleaned_texts = [
            text.strip()
            for text in texts
            if text.strip()
        ]

        if not cleaned_texts:
            raise ValueError("Document texts cannot be empty.")

        return await asyncio.to_thread(
            self._encode,
            cleaned_texts,
        )

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        cleaned_text = text.strip()

        if not cleaned_text:
            raise ValueError("Query text cannot be empty.")

        embeddings = await asyncio.to_thread(
            self._encode,
            [cleaned_text],
        )

        return embeddings[0]

    def _encode(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        model = self._get_model()

        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                self._model_name
            )

        return self._model