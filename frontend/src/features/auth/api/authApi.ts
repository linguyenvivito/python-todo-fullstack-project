import type { ApiRequestOptions, AuthSessionPayload } from "../../../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8888";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T = unknown>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        errorMessage = payload.detail;
      }
    } catch {
      const text = await response.text();
      if (text) {
        errorMessage = text;
      }
    }
    throw new ApiError(errorMessage, response.status);
  }

  return response.json();
}

export function registerUser(username: string, password: string): Promise<unknown> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function loginUser(username: string, password: string): Promise<AuthSessionPayload> {
  return request<AuthSessionPayload>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function refreshUserToken(refreshToken: string): Promise<AuthSessionPayload> {
  return request<AuthSessionPayload>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function revokeUserToken(refreshToken: string): Promise<unknown> {
  return request("/auth/revoke", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export { ApiError };
