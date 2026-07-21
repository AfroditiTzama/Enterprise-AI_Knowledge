import apiClient from "./client";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
}

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
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
  await apiClient.post("/auth/register", credentials);
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiClient.get<CurrentUser>("/auth/me");

  return response.data;
}

export function saveAccessToken(token: string): void {
  localStorage.setItem("access_token", token);
}

export function removeAccessToken(): void {
  localStorage.removeItem("access_token");
}
