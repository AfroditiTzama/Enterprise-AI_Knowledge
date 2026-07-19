import axios from "axios";

export function getApiErrorMessage(
  error: unknown,
): string {
  if (!axios.isAxiosError(error)) {
    return "Something went wrong. Please try again.";
  }

  if (!error.response) {
    return "Cannot connect to the backend API.";
  }

  const data: unknown = error.response.data;

  if (
    typeof data !== "object" ||
    data === null
  ) {
    return "The server returned an unexpected error.";
  }

  const responseData = data as {
    message?: unknown;
    detail?: unknown;
  };

  if (
    typeof responseData.message === "string"
  ) {
    return responseData.message;
  }

  if (
    typeof responseData.detail === "string"
  ) {
    return responseData.detail;
  }

  if (
    Array.isArray(responseData.detail)
  ) {
    const messages: string[] = [];

    for (const item of responseData.detail) {
      if (
        typeof item === "object" &&
        item !== null &&
        "msg" in item
      ) {
        const message = (
          item as { msg?: unknown }
        ).msg;

        if (typeof message === "string") {
          messages.push(message);
        }
      }
    }

    if (messages.length > 0) {
      return messages.join(", ");
    }
  }

  return "The server returned an unexpected error.";
}
