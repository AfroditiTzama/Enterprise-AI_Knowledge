import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 180_000,
});

apiClient.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem("access_token");

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const hasStoredToken = Boolean(
      localStorage.getItem("access_token"),
    );

    if (
      error.response?.status === 401 &&
      hasStoredToken
    ) {
      localStorage.removeItem("access_token");
      window.location.assign("/");
    }

    return Promise.reject(error);
  },
);

export default apiClient;
