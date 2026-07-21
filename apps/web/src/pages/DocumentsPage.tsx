import {
  BookOpen,
  FileCheck2,
  FileText,
  LoaderCircle,
  RefreshCw,
  Trash2,
  Upload,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
} from "react";
import {
  useNavigate,
} from "react-router-dom";

import {
  deleteDocument,
  listDocuments,
  processDocument,
  uploadDocument,
  type DocumentItem,
} from "../api/documents";
import {
  getApiErrorMessage,
} from "../api/errors";
import {
  withApiRetry,
} from "../api/retry";
import {
  compileDocumentWiki,
} from "../api/wiki";
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

type DocumentAction =
  | "process"
  | "compile"
  | "delete";

interface ActiveAction {
  documentId: string;
  action: DocumentAction;
}

export default function DocumentsPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [activeAction, setActiveAction] =
    useState<ActiveAction | null>(null);
  const [documentToDelete, setDocumentToDelete] =
    useState<DocumentItem | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadDocuments = useCallback(async () => {
    setError("");
    setIsLoading(true);
    setIsRetrying(false);

    try {
      const items = await withApiRetry(listDocuments, {
        retries: 2,
        onRetry: () => setIsRetrying(true),
      });
      setDocuments(items);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsLoading(false);
      setIsRetrying(false);
    }
  }, []);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

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
      await loadDocuments();
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
      setNotice(
        `Processing completed: ${result.chunks_count} chunks created.`,
      );
      await loadDocuments();
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
    setActiveAction({
      documentId: document.id,
      action: "delete",
    });

    try {
      await deleteDocument(document.id);
      setDocuments((current) =>
        current.filter((item) => item.id !== document.id),
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
            Upload, process and transform files into connected,
            searchable knowledge.
          </p>
        </div>

        <div className="page-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => void loadDocuments()}
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
          onRetry={() => void loadDocuments()}
        />
      )}

      {notice && (
        <FeedbackBanner kind="success" message={notice} />
      )}

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
            Upload a PDF, DOCX or TXT file. You can process it,
            build Wiki pages and then ask questions in the Assistant.
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
            const isBusy = action !== null;

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

                <div className="document-actions">
                  {document.status !== "PROCESSED" && (
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={isBusy}
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
                    title="Delete document"
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
            ? `${documentToDelete.original_filename} and its extracted chunks and embeddings will be permanently removed. Wiki pages built from shared knowledge may remain.`
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
