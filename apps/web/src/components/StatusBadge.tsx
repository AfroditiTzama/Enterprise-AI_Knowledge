import type {
  DocumentStatus,
} from "../api/documents";

export default function StatusBadge({
  status,
}: {
  status: DocumentStatus;
}) {
  return (
    <span
      className={`status-badge status-${status.toLowerCase()}`}
    >
      {status.toLowerCase()}
    </span>
  );
}
