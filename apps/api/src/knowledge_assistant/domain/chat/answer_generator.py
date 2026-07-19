from abc import ABC, abstractmethod

from knowledge_assistant.domain.chat.entities import (
    GeneratedKnowledgeAnswer,
    RetrievedKnowledgeSource,
)


class KnowledgeAnswerGenerator(ABC):
    @abstractmethod
    async def generate(
        self,
        *,
        question: str,
        sources: tuple[RetrievedKnowledgeSource, ...],
    ) -> GeneratedKnowledgeAnswer:
        """Generate a grounded answer using retrieved sources."""
        raise NotImplementedError