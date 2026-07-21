import axios from "axios";

interface ApiErrorPayload {
  detail?: unknown;
  message?: unknown;
}

type StatusMessages =
  Partial<Record<number, string>>;

function extractErrorDetail(
  detail: unknown,
): string | null {
  if (
    typeof detail === "string" &&
    detail.trim()
  ) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (
          typeof item === "object" &&
          item !== null &&
          "msg" in item &&
          typeof item.msg === "string"
        ) {
          return item.msg;
        }

        return null;
      })
      .filter(
        (message): message is string =>
          message !== null,
      );

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return null;
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
      "The service is temporarily unavailable. " +
      "Please try again shortly."
    );
  }

  const status = error.response.status;

  const customMessage =
    statusMessages[status];

  if (customMessage) {
    return customMessage;
  }

  const payload =
    error.response.data as
      | ApiErrorPayload
      | undefined;

  const detail = extractErrorDetail(
    payload?.detail,
  );

  if (detail) {
    return detail;
  }

  if (
    typeof payload?.message === "string" &&
    payload.message.trim()
  ) {
    return payload.message;
  }

  if (status >= 500) {
    return (
      "The server could not complete the request. " +
      "Please try again."
    );
  }

  return "The request could not be completed.";
}
