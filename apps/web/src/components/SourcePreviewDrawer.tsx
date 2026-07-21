import {
  BookOpen,
  FileText,
  LoaderCircle,
  X,
} from "lucide-react";
import {
  useEffect,
} from "react";
import ReactMarkdown from "react-markdown";

export interface SourcePreviewContent {
  title: string;
  sourceLabel: string;
  locationLabel: string | null;
  text: string;
  score?: number;
  isMarkdown?: boolean;
}

interface SourcePreviewDrawerProps {
  isOpen: boolean;
  isLoading: boolean;
  error: string;
  content: SourcePreviewContent | null;
  onClose: () => void;
}

export default function SourcePreviewDrawer({
  isOpen,
  isLoading,
  error,
  content,
  onClose,
}: SourcePreviewDrawerProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow = "hidden";

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      document.body.style.overflow =
        previousOverflow;

      window.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="source-preview-overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <aside
        className="source-preview-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="source-preview-title"
      >
        <header className="source-preview-header">
          <div className="source-preview-heading">
            <span className="source-preview-icon">
              {content?.isMarkdown ? (
                <BookOpen size={20} />
              ) : (
                <FileText size={20} />
              )}
            </span>

            <div>
              <p>Source preview</p>

              <h2 id="source-preview-title">
                {content?.title ?? "Loading source"}
              </h2>
            </div>
          </div>

          <button
            type="button"
            className="source-preview-close"
            onClick={onClose}
            aria-label="Close source preview"
          >
            <X size={20} />
          </button>
        </header>

        <div className="source-preview-body">
          {isLoading ? (
            <div className="source-preview-loading">
              <LoaderCircle
                className="spin"
                size={24}
              />
              Loading source content...
            </div>
          ) : error ? (
            <div className="error-message">
              {error}
            </div>
          ) : content ? (
            <>
              <div className="source-preview-metadata">
                <span>{content.sourceLabel}</span>

                {content.locationLabel && (
                  <span>
                    {content.locationLabel}
                  </span>
                )}

                {content.score !== undefined && (
                  <span>
                    Relevance{" "}
                    {content.score.toFixed(3)}
                  </span>
                )}
              </div>

              <div className="source-preview-content">
                {content.isMarkdown ? (
                  <div className="markdown-body">
                    <ReactMarkdown>
                      {content.text}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p>{content.text}</p>
                )}
              </div>
            </>
          ) : null}
        </div>
      </aside>
    </div>
  );
}
