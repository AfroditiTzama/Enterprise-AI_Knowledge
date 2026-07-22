from abc import ABC, abstractmethod
from uuid import UUID

from knowledge_assistant.domain.jobs.entities import ProcessingJob


class ProcessingJobRepository(ABC):
    @abstractmethod
    async def add(self, job: ProcessingJob) -> ProcessingJob:
        raise NotImplementedError

    @abstractmethod
    async def update(self, job: ProcessingJob) -> ProcessingJob:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> ProcessingJob | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_for_document(
        self,
        *,
        owner_id: UUID,
        document_id: UUID,
    ) -> ProcessingJob | None:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_for_document(
        self,
        *,
        owner_id: UUID,
        document_id: UUID,
    ) -> ProcessingJob | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_owner_id(
        self,
        owner_id: UUID,
    ) -> list[ProcessingJob]:
        raise NotImplementedError

    @abstractmethod
    async def claim_next_queued(self) -> ProcessingJob | None:
        raise NotImplementedError

    @abstractmethod
    async def recover_interrupted(self) -> int:
        raise NotImplementedError
