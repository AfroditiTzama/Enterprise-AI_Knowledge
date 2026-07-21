import axios from "axios";

interface ApiErrorPayload {
  detail?: unknown;
  message?: unknown;
  error?: unknown;
}

type StatusMessages = Partial<Record<number, string>>;

function extractString(value: unknown): string | null {
  return typeof value === "string" && value.trim()
    ? value.trim()
    : null;
}

function extractErrorDetail(detail: unknown): string | null {
  const direct = extractString(detail);

  if (direct) {
    return direct;
  }

  if (!Array.isArray(detail)) {
    return null;
  }

  const messages = detail
    .map((item) => {
      if (
        typeof item === "object" &&
        item !== null &&
        "msg" in item
      ) {
        return extractString(item.msg);
      }

      return null;
    })
    .filter((message): message is string => message !== null);

  return messages.length > 0 ? messages.join(" ") : null;
}

export function getApiErrorMessage(
  error: unknown,
  statusMessages: StatusMessages = {},
): string {
  if (!axios.isAxiosError(error)) {
    return "Something went wrong. Please try again.";
  }

  if (!error.response) {
    return (
      "We could not reach the server. " +
      "Check your connection and try again."
    );
  }

  const status = error.response.status;
  const customMessage = statusMessages[status];

  if (customMessage) {
    return customMessage;
  }

  const payload = error.response.data as
    | ApiErrorPayload
    | undefined;

  const detail = extractErrorDetail(payload?.detail);
  const message = extractString(payload?.message);

  if (detail) {
    return detail;
  }

  if (message) {
    return message;
  }

  if (status === 401) {
    return "Your session is no longer valid. Please sign in again.";
  }

  if (status === 403) {
    return "You do not have permission to complete this action.";
  }

  if (status === 404) {
    return "The requested resource could not be found.";
  }

  if ([502, 503, 504].includes(status)) {
    return (
      "The server is temporarily unavailable. " +
      "Please try again in a moment."
    );
  }

  if (status >= 500) {
    return (
      "The server could not complete the request. " +
      "Please try again."
    );
  }

  return "The request could not be completed.";
}
