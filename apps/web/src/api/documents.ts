import apiClient from "./client";
import {
  normalizeProcessingJob,
  type ProcessingJob,
} from "./jobs";

export type DocumentStatus =
  | "UPLOADED"
  | "QUEUED"
  | "PROCESSING"
  | "PROCESSED"
  | "FAILED";

interface RawDocumentItem {
  id: string;
  original_filename: string;
  content_type: string | null;
  size_bytes: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: string;
  original_filename: string;
  content_type: string | null;
  size_bytes: number;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

interface RawEnqueueProcessingResponse {
  job: Parameters<typeof normalizeProcessingJob>[0];
  created: boolean;
}

export interface EnqueueProcessingResponse {
  job: ProcessingJob;
  created: boolean;
}

function normalizeStatus(
  status: string,
): DocumentStatus {
  const normalizedStatus =
    status.toUpperCase();

  const validStatuses: DocumentStatus[] = [
    "UPLOADED",
    "QUEUED",
    "PROCESSING",
    "PROCESSED",
    "FAILED",
  ];

  if (
    validStatuses.includes(
      normalizedStatus as DocumentStatus,
    )
  ) {
    return normalizedStatus as DocumentStatus;
  }

  throw new Error(
    `Unknown document status: ${status}`,
  );
}

function normalizeDocument(
  document: RawDocumentItem,
): DocumentItem {
  return {
    ...document,
    status: normalizeStatus(document.status),
  };
}

export async function listDocuments(): Promise<
  DocumentItem[]
> {
  const response =
    await apiClient.get<RawDocumentItem[]>(
      "/documents",
    );

  return response.data.map(
    normalizeDocument,
  );
}

export async function uploadDocument(
  file: File,
): Promise<DocumentItem> {
  const formData = new FormData();

  formData.append("file", file);

  const response =
    await apiClient.post<RawDocumentItem>(
      "/documents",
      formData,
    );

  return normalizeDocument(response.data);
}

export async function processDocument(
  documentId: string,
): Promise<EnqueueProcessingResponse> {
  const response =
    await apiClient.post<RawEnqueueProcessingResponse>(
      `/documents/${documentId}/process`,
    );

  return {
    created: response.data.created,
    job: normalizeProcessingJob(response.data.job),
  };
}

export interface DocumentChunkPreview {
  chunk_id: string;
  document_id: string;
  document_filename: string;
  chunk_index: number;
  page_number: number | null;
  text: string;
}

export async function getDocumentChunkPreview(
  chunkId: string,
): Promise<DocumentChunkPreview> {
  const response =
    await apiClient.get<DocumentChunkPreview>(
      `/documents/chunks/${encodeURIComponent(
        chunkId,
      )}`,
    );

  return response.data;
}

export async function getDocumentChunkPreviewByLocation(
  documentId: string,
  chunkIndex: number,
): Promise<DocumentChunkPreview> {
  const response =
    await apiClient.get<DocumentChunkPreview>(
      `/documents/${encodeURIComponent(
        documentId,
      )}/chunks/${chunkIndex}`,
    );

  return response.data;
}

export async function deleteDocument(
  documentId: string,
): Promise<void> {
  await apiClient.delete(
    `/documents/${encodeURIComponent(documentId)}`,
  );
}
