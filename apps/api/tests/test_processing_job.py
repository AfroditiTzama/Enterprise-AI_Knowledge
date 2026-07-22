from uuid import uuid4

import pytest

from knowledge_assistant.domain.jobs.entities import (
    ProcessingJob,
    ProcessingJobStage,
    ProcessingJobStatus,
)


def test_processing_job_lifecycle() -> None:
    job = ProcessingJob.create_document_processing(
        owner_id=uuid4(),
        document_id=uuid4(),
    )

    assert job.status == ProcessingJobStatus.QUEUED
    assert job.progress == 0

    job.mark_running()
    job.report_progress(
        stage=ProcessingJobStage.CHUNKING,
        progress=40,
    )
    job.mark_completed()

    assert job.status == ProcessingJobStatus.COMPLETED
    assert job.stage == ProcessingJobStage.COMPLETED
    assert job.progress == 100
    assert job.attempts == 1


def test_failed_processing_job_can_be_requeued() -> None:
    job = ProcessingJob.create_document_processing(
        owner_id=uuid4(),
        document_id=uuid4(),
    )

    job.mark_running()
    job.mark_failed("Extraction failed")

    assert job.can_retry is True
    assert job.error_message == "Extraction failed"

    job.requeue()

    assert job.status == ProcessingJobStatus.QUEUED
    assert job.stage == ProcessingJobStage.QUEUED
    assert job.progress == 0
    assert job.error_message is None


def test_completed_job_cannot_be_requeued() -> None:
    job = ProcessingJob.create_document_processing(
        owner_id=uuid4(),
        document_id=uuid4(),
    )
    job.mark_running()
    job.mark_completed()

    with pytest.raises(ValueError, match="cannot be retried"):
        job.requeue()
