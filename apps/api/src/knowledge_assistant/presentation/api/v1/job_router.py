from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_assistant.bootstrap.dependencies.jobs import (
    GetProcessingJobQueryDependency,
    ListProcessingJobsQueryDependency,
    RetryProcessingJobCommandDependency,
)
from knowledge_assistant.bootstrap.dependencies.user import get_current_user
from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.presentation.api.v1.schemas.job import (
    ProcessingJobResponse,
)


router = APIRouter(prefix="/jobs", tags=["Processing jobs"])


@router.get("", response_model=list[ProcessingJobResponse])
async def list_processing_jobs(
    query: ListProcessingJobsQueryDependency,
    current_user: User = Depends(get_current_user),
) -> list[ProcessingJobResponse]:
    jobs = await query.execute(owner_id=current_user.id)
    return [ProcessingJobResponse.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_job(
    job_id: UUID,
    query: GetProcessingJobQueryDependency,
    current_user: User = Depends(get_current_user),
) -> ProcessingJobResponse:
    try:
        job = await query.execute(
            job_id=job_id,
            owner_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return ProcessingJobResponse.model_validate(job)


@router.post(
    "/{job_id}/retry",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_processing_job(
    job_id: UUID,
    command: RetryProcessingJobCommandDependency,
    current_user: User = Depends(get_current_user),
) -> ProcessingJobResponse:
    try:
        job = await command.execute(
            job_id=job_id,
            owner_id=current_user.id,
        )
    except ValueError as error:
        message = str(error)
        http_status = (
            status.HTTP_404_NOT_FOUND
            if message.endswith("was not found.")
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(
            status_code=http_status,
            detail=message,
        ) from error
    return ProcessingJobResponse.model_validate(job)
