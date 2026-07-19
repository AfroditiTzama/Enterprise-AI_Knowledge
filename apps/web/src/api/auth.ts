import apiClient from "./client";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
}

export async function login(
  credentials: LoginRequest,
): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>(
    "/auth/login",
    credentials,
  );

  return response.data;
}

export async function register(
  credentials: RegisterRequest,
): Promise<void> {
  await apiClient.post(
    "/auth/register",
    credentials,
  );
}

export function saveAccessToken(
  token: string,
): void {
  localStorage.setItem("access_token", token);
}

export function removeAccessToken(): void {
  localStorage.removeItem("access_token");
}

export function isAuthenticated(): boolean {
  return Boolean(
    localStorage.getItem("access_token"),
  );
}
