import axios from "axios";

const retriableStatuses = new Set([
  408,
  425,
  429,
  500,
  502,
  503,
  504,
]);

export function isRetriableApiError(
  error: unknown,
): boolean {
  if (!axios.isAxiosError(error)) {
    return false;
  }

  if (!error.response) {
    return true;
  }

  return retriableStatuses.has(error.response.status);
}

interface RetryOptions {
  retries?: number;
  baseDelayMs?: number;
  onRetry?: (attempt: number) => void;
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}

export async function withApiRetry<T>(
  operation: () => Promise<T>,
  options: RetryOptions = {},
): Promise<T> {
  const retries = options.retries ?? 2;
  const baseDelayMs = options.baseDelayMs ?? 700;

  let attempt = 0;

  while (true) {
    try {
      return await operation();
    } catch (error) {
      if (
        attempt >= retries ||
        !isRetriableApiError(error)
      ) {
        throw error;
      }

      attempt += 1;
      options.onRetry?.(attempt);
      await wait(baseDelayMs * attempt);
    }
  }
}
