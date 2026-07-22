import {
  GitCompareArrows,
  LoaderCircle,
  RotateCcw,
  X,
} from "lucide-react";
import { useEffect } from "react";

import type { WikiRevisionDiff } from "../api/wiki";

interface RevisionDiffDrawerProps {
  isOpen: boolean;
  isLoading: boolean;
  isRestoring: boolean;
  error: string;
  diff: WikiRevisionDiff | null;
  onRestore: () => void;
  onClose: () => void;
}

export default function RevisionDiffDrawer({
  isOpen,
  isLoading,
  isRestoring,
  error,
  diff,
  onRestore,
  onClose,
}: RevisionDiffDrawerProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isRestoring) {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, isRestoring, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="source-preview-overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !isRestoring
        ) {
          onClose();
        }
      }}
    >
      <aside
        className="source-preview-drawer revision-diff-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="revision-diff-title"
      >
        <header className="source-preview-header">
          <div className="source-preview-heading">
            <span className="source-preview-icon">
              <GitCompareArrows size={20} />
            </span>

            <div>
              <p>Revision comparison</p>
              <h2 id="revision-diff-title">
                {diff
                  ? `Version ${diff.to_revision_number}`
                  : "Loading changes"}
              </h2>
            </div>
          </div>

          <button
            type="button"
            className="source-preview-close"
            onClick={onClose}
            disabled={isRestoring}
            aria-label="Close revision comparison"
          >
            <X size={20} />
          </button>
        </header>

        <div className="source-preview-body">
          {isLoading ? (
            <div className="source-preview-loading">
              <LoaderCircle className="spin" size={24} />
              Loading revision changes...
            </div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : diff ? (
            <>
              <div className="source-preview-metadata">
                <span>
                  {diff.from_revision_number === null
                    ? "Initial version"
                    : `v${diff.from_revision_number} → v${diff.to_revision_number}`}
                </span>
              </div>

              <div className="revision-diff-content">
                {diff.lines.length === 0 ? (
                  <p className="muted-copy">
                    No textual changes were detected.
                  </p>
                ) : (
                  diff.lines.map((line, index) => (
                    <div
                      className={`revision-diff-line ${line.kind}`}
                      key={`${index}-${line.text}`}
                    >
                      <span>
                        {line.kind === "added"
                          ? "+"
                          : line.kind === "removed"
                            ? "−"
                            : " "}
                      </span>
                      <code>{line.text || " "}</code>
                    </div>
                  ))
                )}
              </div>

              <div className="revision-diff-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={onClose}
                  disabled={isRestoring}
                >
                  Close
                </button>
                <button
                  type="button"
                  className="primary-button compact"
                  onClick={onRestore}
                  disabled={isRestoring}
                >
                  {isRestoring ? (
                    <LoaderCircle className="spin" size={17} />
                  ) : (
                    <RotateCcw size={17} />
                  )}
                  Restore this version
                </button>
              </div>
            </>
          ) : null}
        </div>
      </aside>
    </div>
  );
}
