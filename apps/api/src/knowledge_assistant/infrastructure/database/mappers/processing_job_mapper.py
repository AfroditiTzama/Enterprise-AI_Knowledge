from knowledge_assistant.domain.jobs.entities import ProcessingJob
from knowledge_assistant.infrastructure.database.models.processing_job import (
    ProcessingJobModel,
)


class ProcessingJobMapper:
    @staticmethod
    def to_domain(model: ProcessingJobModel) -> ProcessingJob:
        return ProcessingJob(
            id=model.id,
            owner_id=model.owner_id,
            document_id=model.document_id,
            job_type=model.job_type,
            status=model.status,
            stage=model.stage,
            progress=model.progress,
            attempts=model.attempts,
            max_attempts=model.max_attempts,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
        )

    @staticmethod
    def to_model(entity: ProcessingJob) -> ProcessingJobModel:
        return ProcessingJobModel(
            id=entity.id,
            owner_id=entity.owner_id,
            document_id=entity.document_id,
            job_type=entity.job_type,
            status=entity.status,
            stage=entity.stage,
            progress=entity.progress,
            attempts=entity.attempts,
            max_attempts=entity.max_attempts,
            error_message=entity.error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
        )
