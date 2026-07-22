from uuid import UUID

from knowledge_assistant.domain.documents.repository import DocumentRepository
from knowledge_assistant.domain.jobs.entities import ProcessingJob
from knowledge_assistant.domain.jobs.repository import ProcessingJobRepository


class RetryProcessingJobCommand:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        job_repository: ProcessingJobRepository,
    ) -> None:
        self._document_repository = document_repository
        self._job_repository = job_repository

    async def execute(
        self,
        *,
        job_id: UUID,
        owner_id: UUID,
    ) -> ProcessingJob:
        job = await self._job_repository.get_by_id(job_id)
        if job is None or job.owner_id != owner_id:
            raise ValueError("Processing job was not found.")

        document = await self._document_repository.get_by_id(job.document_id)
        if document is None or document.owner_id != owner_id:
            raise ValueError("Document was not found.")

        active_job = await self._job_repository.get_active_for_document(
            owner_id=owner_id,
            document_id=job.document_id,
        )
        if active_job is not None and active_job.id != job.id:
            raise ValueError(
                "This document already has an active processing job."
            )

        job.requeue()
        document.mark_as_queued()
        await self._document_repository.update(document)
        return await self._job_repository.update(job)
