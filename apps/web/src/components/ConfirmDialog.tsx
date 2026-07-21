import {
  AlertTriangle,
  LoaderCircle,
  X,
} from "lucide-react";
import {
  useEffect,
} from "react";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  isBusy?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export default function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmLabel,
  isBusy = false,
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isBusy) {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isBusy, isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="dialog-overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !isBusy
        ) {
          onClose();
        }
      }}
    >
      <section
        className="confirm-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <header>
          <span className="dialog-warning-icon">
            <AlertTriangle size={22} />
          </span>

          <button
            type="button"
            className="icon-ghost-button"
            onClick={onClose}
            disabled={isBusy}
            aria-label="Close confirmation dialog"
          >
            <X size={19} />
          </button>
        </header>

        <h2 id="confirm-dialog-title">{title}</h2>
        <p>{description}</p>

        <footer>
          <button
            type="button"
            className="secondary-button"
            onClick={onClose}
            disabled={isBusy}
          >
            Cancel
          </button>

          <button
            type="button"
            className="danger-button"
            onClick={onConfirm}
            disabled={isBusy}
          >
            {isBusy && (
              <LoaderCircle className="spin" size={17} />
            )}
            {confirmLabel}
          </button>
        </footer>
      </section>
    </div>
  );
}
