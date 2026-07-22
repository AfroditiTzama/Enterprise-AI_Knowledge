from uuid import UUID

from knowledge_assistant.domain.jobs.entities import ProcessingJob
from knowledge_assistant.domain.jobs.repository import ProcessingJobRepository


class ListProcessingJobsQuery:
    def __init__(self, repository: ProcessingJobRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        owner_id: UUID,
    ) -> list[ProcessingJob]:
        return await self._repository.list_by_owner_id(owner_id)
