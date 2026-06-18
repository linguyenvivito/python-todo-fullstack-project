import type { ApiRequestOptions, AuthSessionPayload } from "../../../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8888";

export class ApiError extends Error {
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

/**
 * Register a new user.
 */
export function registerUser(username: string, password: string): Promise<unknown> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

/**
 * Login a user and get tokens.
 */
export function loginUser(username: string, password: string): Promise<AuthSessionPayload> {
  return request<AuthSessionPayload>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

/**
 * Refresh the access token using a refresh token.
 */
export function refreshUserToken(refreshToken: string): Promise<AuthSessionPayload> {
  return request<AuthSessionPayload>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

/**
 * Revoke a refresh token (logout).
 */
export function revokeUserToken(refreshToken: string): Promise<unknown> {
  return request("/auth/revoke", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

/**
 * Business logic for authentication operations.
 */

export type AuthSessionPayloadType = {
  user: {
    username: string;
  };
  access_token: string;
  refresh_token: string;
};

/**
 * Validate credentials (username and password).
 */
export function validateCredentials(username: string, password: string): void {
  const trimmedUsername = username.trim();
  const trimmedPassword = password.trim();

  if (!trimmedUsername || !trimmedPassword) {
    throw new Error("Username and password are required");
  }
}

/**
 * Login and apply session from response payload.
 */
export async function loginAndApplySession(
  username: string,
  password: string,
  applySession: (payload: AuthSessionPayloadType) => any
): Promise<any> {
  validateCredentials(username, password);
  const payload = await loginUser(username.trim(), password.trim());
  return applySession(payload);
}

/**
 * Register a new user and then login.
 */
export async function registerAndLogin(
  username: string,
  password: string,
  applySession: (payload: AuthSessionPayloadType) => any
): Promise<any> {
  validateCredentials(username, password);
  await registerUser(username.trim(), password.trim());
  return loginAndApplySession(username, password, applySession);
}

/**
 * Refresh access token if refresh token exists.
 */
export async function refreshAccessTokenWithRetry(
  currentSession: any,
  getStoredSession: () => any,
  applySession: (payload: AuthSessionPayloadType) => any,
  clearSession: () => void
): Promise<string> {
  const session = currentSession || getStoredSession();
  if (!session?.refreshToken) {
    clearSession();
    throw new Error("Session expired. Please sign in again.");
  }

  try {
    const payload = await refreshUserToken(session.refreshToken);
    const nextSession = applySession(payload);
    return nextSession.accessToken;
  } catch (err) {
    clearSession();
    throw err;
  }
}

/**
 * Execute authenticated request with auto-retry on 401 (token refresh).
 */
export async function executeWithTokenRefresh<T>(
  currentSession: any,
  getStoredSession: () => any,
  applySession: (payload: AuthSessionPayloadType) => any,
  clearSession: () => void,
  operation: (token: string) => Promise<T>
): Promise<T> {
  const session = currentSession || getStoredSession();
  if (!session?.accessToken) {
    throw new Error("Session expired. Please sign in again.");
  }

  try {
    return await operation(session.accessToken);
  } catch (err) {
    if (!(err instanceof ApiError) || err.status !== 401 || !session.refreshToken) {
      throw err;
    }

    const refreshedAccessToken = await refreshAccessTokenWithRetry(
      currentSession,
      getStoredSession,
      applySession,
      clearSession
    );
    return operation(refreshedAccessToken);
  }
}

/**
 * Logout: revoke token and clear session.
 */
export async function logout(
  currentSession: any,
  getStoredSession: () => any,
  clearSession: () => void
): Promise<void> {
  const session = currentSession || getStoredSession();
  if (session?.refreshToken) {
    try {
      await revokeUserToken(session.refreshToken);
    } catch {
      // Ignore revoke failures and clear local state anyway.
    }
  }

  clearSession();
}
