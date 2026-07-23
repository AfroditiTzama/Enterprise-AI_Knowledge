from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from knowledge_assistant.domain.usage.entities import (
    LLMUsageEvent,
    LLMUsageSummary,
)


class LLMUsageRepository(ABC):
    @abstractmethod
    async def add(self, event: LLMUsageEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def summarize(
        self,
        *,
        owner_id: UUID,
        since: datetime,
    ) -> LLMUsageSummary:
        raise NotImplementedError
