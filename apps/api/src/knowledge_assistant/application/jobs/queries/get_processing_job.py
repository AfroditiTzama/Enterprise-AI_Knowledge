from uuid import UUID

from knowledge_assistant.domain.jobs.entities import ProcessingJob
from knowledge_assistant.domain.jobs.repository import ProcessingJobRepository


class GetProcessingJobQuery:
    def __init__(self, repository: ProcessingJobRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        job_id: UUID,
        owner_id: UUID,
    ) -> ProcessingJob:
        job = await self._repository.get_by_id(job_id)
        if job is None or job.owner_id != owner_id:
            raise ValueError("Processing job was not found.")
        return job
