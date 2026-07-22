import {
  BookOpen,
  FileCheck2,
  FileText,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
  Trash2,
  Upload,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  deleteDocument,
  listDocuments,
  processDocument,
  uploadDocument,
  type DocumentItem,
} from "../api/documents";
import { getApiErrorMessage } from "../api/errors";
import {
  listProcessingJobs,
  retryProcessingJob,
  type ProcessingJob,
  type ProcessingJobStage,
} from "../api/jobs";
import { withApiRetry } from "../api/retry";
import { compileDocumentWiki } from "../api/wiki";
import ConfirmDialog from "../components/ConfirmDialog";
import FeedbackBanner from "../components/FeedbackBanner";
import StatusBadge from "../components/StatusBadge";
import WorkflowSteps from "../components/WorkflowSteps";

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kilobytes = bytes / 1024;

  if (kilobytes < 1024) {
    return `${kilobytes.toFixed(1)} KB`;
  }

  return `${(kilobytes / 1024).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  }).format(new Date(value));
}

const stageLabels: Record<ProcessingJobStage, string> = {
  QUEUED: "Waiting in queue",
  EXTRACTING: "Extracting text",
  CHUNKING: "Creating chunks",
  EMBEDDING: "Generating embeddings",
  PERSISTING: "Saving knowledge",
  COMPLETED: "Processing complete",
};

type DocumentAction = "process" | "compile" | "delete" | "retry";

interface ActiveAction {
  documentId: string;
  action: DocumentAction;
}

function latestJobsByDocument(
  jobs: ProcessingJob[],
): Record<string, ProcessingJob> {
  const result: Record<string, ProcessingJob> = {};

  for (const job of jobs) {
    if (!result[job.document_id]) {
      result[job.document_id] = job;
    }
  }

  return result;
}

export default function DocumentsPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [activeAction, setActiveAction] =
    useState<ActiveAction | null>(null);
  const [documentToDelete, setDocumentToDelete] =
    useState<DocumentItem | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const jobsByDocument = useMemo(
    () => latestJobsByDocument(jobs),
    [jobs],
  );

  const hasActiveJobs = jobs.some(
    (job) => job.status === "QUEUED" || job.status === "RUNNING",
  );

  const loadWorkspace = useCallback(
    async ({ showLoading = true }: { showLoading?: boolean } = {}) => {
      setError("");
      if (showLoading) {
        setIsLoading(true);
        setIsRetrying(false);
      }

      try {
        const [documentItems, processingJobs] = await withApiRetry(
          async () => Promise.all([
            listDocuments(),
            listProcessingJobs(),
          ]),
          {
            retries: 2,
            onRetry: () => {
              if (showLoading) {
                setIsRetrying(true);
              }
            },
          },
        );
        setDocuments(documentItems);
        setJobs(processingJobs);
      } catch (requestError) {
        setError(getApiErrorMessage(requestError));
      } finally {
        if (showLoading) {
          setIsLoading(false);
          setIsRetrying(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  useEffect(() => {
    if (!hasActiveJobs) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadWorkspace({ showLoading: false });
    }, 1500);

    return () => window.clearInterval(intervalId);
  }, [hasActiveJobs, loadWorkspace]);

  async function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setError("");
    setNotice("");
    setIsUploading(true);

    try {
      await uploadDocument(file);
      setNotice(`${file.name} uploaded successfully.`);
      await loadWorkspace({ showLoading: false });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  }

  async function handleProcess(documentId: string) {
    setError("");
    setNotice("");
    setActiveAction({ documentId, action: "process" });

    try {
      const result = await processDocument(documentId);
      setJobs((current) => [
        result.job,
        ...current.filter((job) => job.id !== result.job.id),
      ]);
      setNotice(
        result.created
          ? "Document processing was added to the local queue."
          : "This document is already being processed.",
      );
      await loadWorkspace({ showLoading: false });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setActiveAction(null);
    }
  }

  async function handleRetry(job: ProcessingJob) {
    setError("");
    setNotice("");
    setActiveAction({ documentId: job.document_id, action: "retry" });

    try {
      const updatedJob = await retryProcessingJob(job.id);
      setJobs((current) => [
        updatedJob,
        ...current.filter((item) => item.id !== updatedJob.id),
      ]);
      setNotice("Processing was queued again.");
      await loadWorkspace({ showLoading: false });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setActiveAction(null);
    }
  }

  async function handleCompile(documentId: string) {
    setError("");
    setNotice("");
    setActiveAction({ documentId, action: "compile" });

    try {
      const result = await compileDocumentWiki(documentId);
      setNotice(`Wiki updated with ${result.pages_count} pages.`);
      navigate("/wiki");
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setActiveAction(null);
    }
  }

  async function confirmDelete() {
    if (!documentToDelete) {
      return;
    }

    const document = documentToDelete;
    setError("");
    setNotice("");
    setActiveAction({ documentId: document.id, action: "delete" });

    try {
      await deleteDocument(document.id);
      setDocuments((current) =>
        current.filter((item) => item.id !== document.id),
      );
      setJobs((current) =>
        current.filter((job) => job.document_id !== document.id),
      );
      setNotice(`${document.original_filename} was deleted.`);
      setDocumentToDelete(null);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setActiveAction(null);
    }
  }

  const openFilePicker = () => fileInputRef.current?.click();

  return (
    <section className="page-container">
      <header className="page-header">
        <div>
          <p className="eyebrow">Knowledge workspace</p>
          <h1>Your documents</h1>
          <p>
            Upload files and let the local worker process them safely in
            the background.
          </p>
        </div>

        <div className="page-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => void loadWorkspace()}
            disabled={isLoading}
          >
            <RefreshCw size={17} />
            Refresh
          </button>

          <button
            type="button"
            className="primary-button compact"
            disabled={isUploading}
            onClick={openFilePicker}
          >
            {isUploading ? (
              <LoaderCircle className="spin" size={18} />
            ) : (
              <Upload size={18} />
            )}
            {isUploading ? "Uploading..." : "Upload document"}
          </button>

          <input
            ref={fileInputRef}
            className="visually-hidden"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
          />
        </div>
      </header>

      <WorkflowSteps />

      {isRetrying && (
        <FeedbackBanner
          kind="retrying"
          message="The server is waking up. Retrying…"
        />
      )}

      {error && !isRetrying && (
        <FeedbackBanner
          kind="error"
          message={error}
          onRetry={() => void loadWorkspace()}
        />
      )}

      {notice && <FeedbackBanner kind="success" message={notice} />}

      {isLoading && !isRetrying ? (
        <div className="document-grid" aria-label="Loading documents">
          {[0, 1, 2].map((item) => (
            <div className="document-card skeleton-card" key={item} />
          ))}
        </div>
      ) : error ? null : documents.length === 0 ? (
        <section className="empty-state">
          <div className="empty-icon">
            <FileText size={30} />
          </div>
          <h2>Start with your first document</h2>
          <p>
            Upload a PDF, DOCX or TXT file. Processing continues in the
            background even while you browse another page.
          </p>
          <button
            type="button"
            className="primary-button compact"
            onClick={openFilePicker}
          >
            <Upload size={18} />
            Upload document
          </button>
        </section>
      ) : (
        <div className="document-grid">
          {documents.map((document) => {
            const action =
              activeAction?.documentId === document.id
                ? activeAction.action
                : null;
            const job = jobsByDocument[document.id];
            const isJobActive =
              job?.status === "QUEUED" || job?.status === "RUNNING";
            const isBusy = action !== null || isJobActive;

            return (
              <article className="document-card" key={document.id}>
                <div className="document-card-top">
                  <div className="document-icon">
                    <FileText size={22} />
                  </div>
                  <StatusBadge status={document.status} />
                </div>

                <div className="document-card-content">
                  <h2 title={document.original_filename}>
                    {document.original_filename}
                  </h2>
                  <div className="document-meta">
                    <span>{formatBytes(document.size_bytes)}</span>
                    <span>{formatDate(document.created_at)}</span>
                  </div>
                </div>

                {job && (job.status === "QUEUED" || job.status === "RUNNING") && (
                  <div className="processing-progress" aria-live="polite">
                    <div className="processing-progress-header">
                      <span>{stageLabels[job.stage]}</span>
                      <strong>{job.progress}%</strong>
                    </div>
                    <div
                      className="processing-progress-track"
                      role="progressbar"
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={job.progress}
                    >
                      <span style={{ width: `${job.progress}%` }} />
                    </div>
                    <small>
                      Attempt {job.attempts || 1} of {job.max_attempts}
                    </small>
                  </div>
                )}

                {job?.status === "FAILED" && (
                  <div className="processing-failure">
                    <strong>Processing failed</strong>
                    <p>{job.error_message || "The document could not be processed."}</p>
                    <button
                      type="button"
                      className="secondary-button compact"
                      disabled={action === "retry" || job.attempts >= job.max_attempts}
                      onClick={() => void handleRetry(job)}
                    >
                      {action === "retry" ? (
                        <LoaderCircle className="spin" size={16} />
                      ) : (
                        <RotateCcw size={16} />
                      )}
                      Retry processing
                    </button>
                  </div>
                )}

                <div className="document-actions">
                  {document.status !== "PROCESSED" && !isJobActive && (
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={isBusy || job?.status === "FAILED"}
                      onClick={() => void handleProcess(document.id)}
                    >
                      {action === "process" ? (
                        <LoaderCircle className="spin" size={16} />
                      ) : (
                        <FileCheck2 size={16} />
                      )}
                      Process
                    </button>
                  )}

                  {document.status === "PROCESSED" && (
                    <button
                      type="button"
                      className="primary-button compact"
                      disabled={isBusy}
                      onClick={() => void handleCompile(document.id)}
                    >
                      {action === "compile" ? (
                        <LoaderCircle className="spin" size={16} />
                      ) : (
                        <BookOpen size={16} />
                      )}
                      Build Wiki
                    </button>
                  )}

                  <button
                    type="button"
                    className="icon-ghost-button danger-text"
                    disabled={isBusy}
                    onClick={() => setDocumentToDelete(document)}
                    aria-label={`Delete ${document.original_filename}`}
                    title={
                      isJobActive
                        ? "Wait for processing to finish before deleting"
                        : "Delete document"
                    }
                  >
                    {action === "delete" ? (
                      <LoaderCircle className="spin" size={17} />
                    ) : (
                      <Trash2 size={17} />
                    )}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <ConfirmDialog
        isOpen={documentToDelete !== null}
        title="Delete this document?"
        description={
          documentToDelete
            ? `${documentToDelete.original_filename} and its extracted chunks, embeddings and processing history will be permanently removed. Wiki pages built from shared knowledge may remain.`
            : ""
        }
        confirmLabel="Delete document"
        isBusy={activeAction?.action === "delete"}
        onConfirm={() => void confirmDelete()}
        onClose={() => setDocumentToDelete(null)}
      />
    </section>
  );
}
