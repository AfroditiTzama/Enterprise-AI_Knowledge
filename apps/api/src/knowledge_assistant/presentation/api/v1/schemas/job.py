from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from knowledge_assistant.domain.jobs.entities import (
    ProcessingJobStage,
    ProcessingJobStatus,
    ProcessingJobType,
)


class ProcessingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    document_id: UUID
    job_type: ProcessingJobType
    status: ProcessingJobStatus
    stage: ProcessingJobStage
    progress: int
    attempts: int
    max_attempts: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class EnqueueProcessingJobResponse(BaseModel):
    job: ProcessingJobResponse
    created: bool
