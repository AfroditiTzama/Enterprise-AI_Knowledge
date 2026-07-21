import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 180_000,
});

apiClient.interceptors.request.use((config) => {
  const accessToken =
    localStorage.getItem("access_token");

  if (accessToken) {
    config.headers.Authorization =
      `Bearer ${accessToken}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status =
      error.response?.status;

    const requestUrl =
      String(error.config?.url ?? "");

    const isAuthenticationRequest =
      requestUrl.includes("/auth/login") ||
      requestUrl.includes("/auth/register");

    const hasStoredToken = Boolean(
      localStorage.getItem("access_token"),
    );

    if (
      status === 401 &&
      hasStoredToken &&
      !isAuthenticationRequest
    ) {
      localStorage.removeItem(
        "access_token",
      );

      sessionStorage.setItem(
        "auth_notice",
        (
          "Your session has expired. " +
          "Please sign in again."
        ),
      );

      window.location.assign("/");
    }

    return Promise.reject(error);
  },
);

export default apiClient;
