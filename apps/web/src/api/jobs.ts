import apiClient from "./client";

export type ProcessingJobStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type ProcessingJobStage =
  | "QUEUED"
  | "EXTRACTING"
  | "CHUNKING"
  | "EMBEDDING"
  | "PERSISTING"
  | "COMPLETED";

interface RawProcessingJob {
  id: string;
  owner_id: string;
  document_id: string;
  job_type: string;
  status: string;
  stage: string;
  progress: number;
  attempts: number;
  max_attempts: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ProcessingJob {
  id: string;
  owner_id: string;
  document_id: string;
  job_type: "DOCUMENT_PROCESSING";
  status: ProcessingJobStatus;
  stage: ProcessingJobStage;
  progress: number;
  attempts: number;
  max_attempts: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

function normalizeEnum<T extends string>(value: string): T {
  return value.toUpperCase() as T;
}

export function normalizeProcessingJob(
  job: RawProcessingJob,
): ProcessingJob {
  return {
    ...job,
    job_type: normalizeEnum<"DOCUMENT_PROCESSING">(
      job.job_type,
    ),
    status: normalizeEnum<ProcessingJobStatus>(job.status),
    stage: normalizeEnum<ProcessingJobStage>(job.stage),
  };
}

export async function listProcessingJobs(): Promise<ProcessingJob[]> {
  const response = await apiClient.get<RawProcessingJob[]>("/jobs");
  return response.data.map(normalizeProcessingJob);
}

export async function getProcessingJob(
  jobId: string,
): Promise<ProcessingJob> {
  const response = await apiClient.get<RawProcessingJob>(
    `/jobs/${encodeURIComponent(jobId)}`,
  );
  return normalizeProcessingJob(response.data);
}

export async function retryProcessingJob(
  jobId: string,
): Promise<ProcessingJob> {
  const response = await apiClient.post<RawProcessingJob>(
    `/jobs/${encodeURIComponent(jobId)}/retry`,
  );
  return normalizeProcessingJob(response.data);
}
