from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_assistant.application.jobs.commands.enqueue_document_processing import (
    EnqueueDocumentProcessingCommand,
)
from knowledge_assistant.application.jobs.commands.retry_processing_job import (
    RetryProcessingJobCommand,
)
from knowledge_assistant.application.jobs.queries.get_processing_job import (
    GetProcessingJobQuery,
)
from knowledge_assistant.application.jobs.queries.list_processing_jobs import (
    ListProcessingJobsQuery,
)
from knowledge_assistant.bootstrap.dependencies.document import (
    get_document_repository,
)
from knowledge_assistant.domain.documents.repository import DocumentRepository
from knowledge_assistant.domain.jobs.repository import ProcessingJobRepository
from knowledge_assistant.infrastructure.database.repositories.processing_job_repository import (
    SQLAlchemyProcessingJobRepository,
)
from knowledge_assistant.infrastructure.database.session import get_db_session


def get_processing_job_repository(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> ProcessingJobRepository:
    return SQLAlchemyProcessingJobRepository(session)


def get_enqueue_document_processing_command(
    document_repository: Annotated[
        DocumentRepository,
        Depends(get_document_repository),
    ],
    job_repository: Annotated[
        ProcessingJobRepository,
        Depends(get_processing_job_repository),
    ],
) -> EnqueueDocumentProcessingCommand:
    return EnqueueDocumentProcessingCommand(
        document_repository=document_repository,
        job_repository=job_repository,
    )


def get_retry_processing_job_command(
    document_repository: Annotated[
        DocumentRepository,
        Depends(get_document_repository),
    ],
    job_repository: Annotated[
        ProcessingJobRepository,
        Depends(get_processing_job_repository),
    ],
) -> RetryProcessingJobCommand:
    return RetryProcessingJobCommand(
        document_repository=document_repository,
        job_repository=job_repository,
    )


def get_list_processing_jobs_query(
    repository: Annotated[
        ProcessingJobRepository,
        Depends(get_processing_job_repository),
    ],
) -> ListProcessingJobsQuery:
    return ListProcessingJobsQuery(repository)


def get_processing_job_query(
    repository: Annotated[
        ProcessingJobRepository,
        Depends(get_processing_job_repository),
    ],
) -> GetProcessingJobQuery:
    return GetProcessingJobQuery(repository)


ProcessingJobRepositoryDependency = Annotated[
    ProcessingJobRepository,
    Depends(get_processing_job_repository),
]
EnqueueDocumentProcessingCommandDependency = Annotated[
    EnqueueDocumentProcessingCommand,
    Depends(get_enqueue_document_processing_command),
]
RetryProcessingJobCommandDependency = Annotated[
    RetryProcessingJobCommand,
    Depends(get_retry_processing_job_command),
]
ListProcessingJobsQueryDependency = Annotated[
    ListProcessingJobsQuery,
    Depends(get_list_processing_jobs_query),
]
GetProcessingJobQueryDependency = Annotated[
    GetProcessingJobQuery,
    Depends(get_processing_job_query),
]
