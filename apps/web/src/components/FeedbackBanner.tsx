import {
  AlertCircle,
  CheckCircle2,
  LoaderCircle,
  RotateCcw,
} from "lucide-react";

interface FeedbackBannerProps {
  kind: "error" | "success" | "retrying";
  message: string;
  onRetry?: () => void;
}

export default function FeedbackBanner({
  kind,
  message,
  onRetry,
}: FeedbackBannerProps) {
  const Icon =
    kind === "error"
      ? AlertCircle
      : kind === "success"
        ? CheckCircle2
        : LoaderCircle;

  return (
    <div
      className={`feedback-banner feedback-${kind}`}
      role={kind === "error" ? "alert" : "status"}
    >
      <Icon
        size={19}
        className={kind === "retrying" ? "spin" : ""}
      />

      <span>{message}</span>

      {onRetry && (
        <button
          type="button"
          className="inline-action"
          onClick={onRetry}
        >
          <RotateCcw size={15} />
          Retry
        </button>
      )}
    </div>
  );
}
