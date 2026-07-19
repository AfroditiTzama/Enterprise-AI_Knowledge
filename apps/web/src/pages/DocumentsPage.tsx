import {
  BookOpen,
  FileText,
  LoaderCircle,
  RefreshCw,
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
  listDocuments,
  processDocument,
  uploadDocument,
  type DocumentItem,
} from "../api/documents";
import {
  getApiErrorMessage,
} from "../api/errors";
import {
  compileDocumentWiki,
} from "../api/wiki";
import StatusBadge from "../components/StatusBadge";

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
  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(new Date(value));
}

export default function DocumentsPage() {
  const navigate = useNavigate();
  const fileInputRef =
    useRef<HTMLInputElement | null>(null);

  const [documents, setDocuments] =
    useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] =
    useState(true);
  const [isUploading, setIsUploading] =
    useState(false);
  const [activeDocumentId, setActiveDocumentId] =
    useState<string | null>(null);
  const [error, setError] =
    useState("");
  const [notice, setNotice] =
    useState("");

  const loadDocuments = useCallback(async () => {
    setError("");

    try {
      const items = await listDocuments();
      setDocuments(items);
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setIsLoading(false);
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
      setNotice(
        `${file.name} uploaded successfully.`,
      );
      await loadDocuments();
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  }

  async function handleProcess(
    documentId: string,
  ) {
    setError("");
    setNotice("");
    setActiveDocumentId(documentId);

    try {
      const result =
        await processDocument(documentId);

      setNotice(
        `Processing completed: ${result.chunks_count} chunks created.`,
      );

      await loadDocuments();
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setActiveDocumentId(null);
    }
  }

  async function handleCompile(
    documentId: string,
  ) {
    setError("");
    setNotice("");
    setActiveDocumentId(documentId);

    try {
      const result =
        await compileDocumentWiki(documentId);

      setNotice(
        `Wiki created with ${result.pages_count} pages.`,
      );

      navigate("/wiki");
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setActiveDocumentId(null);
    }
  }

  return (
    <section className="page-container">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Knowledge workspace
          </p>

          <h1>Your documents</h1>

          <p>
            Upload, process and transform
            documents into connected Wiki
            knowledge.
          </p>
        </div>

        <div className="page-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() =>
              void loadDocuments()
            }
          >
            <RefreshCw size={17} />
            Refresh
          </button>

          <button
            type="button"
            className="primary-button compact"
            disabled={isUploading}
            onClick={() =>
              fileInputRef.current?.click()
            }
          >
            {isUploading ? (
              <LoaderCircle
                className="spin"
                size={18}
              />
            ) : (
              <Upload size={18} />
            )}

            {isUploading
              ? "Uploading..."
              : "Upload document"}
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

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {notice && (
        <div className="success-message">
          {notice}
        </div>
      )}

      {isLoading ? (
        <div className="loading-panel">
          <LoaderCircle
            className="spin"
            size={28}
          />
          Loading documents...
        </div>
      ) : documents.length === 0 ? (
        <section className="empty-state">
          <div className="empty-icon">
            <FileText size={30} />
          </div>

          <h2>No documents yet</h2>

          <p>
            Upload a PDF, DOCX or TXT file to
            begin building your internal
            knowledge base.
          </p>
        </section>
      ) : (
        <div className="document-grid">
          {documents.map((document) => {
            const isBusy =
              activeDocumentId === document.id;

            return (
              <article
                className="document-card"
                key={document.id}
              >
                <div className="document-card-top">
                  <div className="document-icon">
                    <FileText size={22} />
                  </div>

                  <StatusBadge
                    status={document.status}
                  />
                </div>

                <h2>
                  {document.original_filename}
                </h2>

                <div className="document-meta">
                  <span>
                    {formatBytes(
                      document.size_bytes,
                    )}
                  </span>
                  <span>
                    {formatDate(
                      document.created_at,
                    )}
                  </span>
                </div>

                <div className="document-actions">
                  {document.status !==
                    "PROCESSED" && (
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={isBusy}
                      onClick={() =>
                        void handleProcess(
                          document.id,
                        )
                      }
                    >
                      {isBusy ? (
                        <LoaderCircle
                          className="spin"
                          size={16}
                        />
                      ) : (
                        <RefreshCw size={16} />
                      )}

                      Process
                    </button>
                  )}

                  {document.status ===
                    "PROCESSED" && (
                    <button
                      type="button"
                      className="primary-button compact"
                      disabled={isBusy}
                      onClick={() =>
                        void handleCompile(
                          document.id,
                        )
                      }
                    >
                      {isBusy ? (
                        <LoaderCircle
                          className="spin"
                          size={16}
                        />
                      ) : (
                        <BookOpen size={16} />
                      )}

                      Build Wiki
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
