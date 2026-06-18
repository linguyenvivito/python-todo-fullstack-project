import { loginUser, registerUser, refreshUserToken, revokeUserToken, ApiError } from "../api/authApi";
import type { StoredSession } from "../storage/session";

export type AuthSessionPayload = {
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
  applySession: (payload: AuthSessionPayload) => StoredSession
): Promise<StoredSession> {
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
  applySession: (payload: AuthSessionPayload) => StoredSession
): Promise<StoredSession> {
  validateCredentials(username, password);
  await registerUser(username.trim(), password.trim());
  return loginAndApplySession(username, password, applySession);
}

/**
 * Refresh access token if refresh token exists.
 */
export async function refreshAccessTokenWithRetry(
  currentSession: StoredSession | null,
  getStoredSession: () => StoredSession | null,
  applySession: (payload: AuthSessionPayload) => StoredSession,
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
  currentSession: StoredSession | null,
  getStoredSession: () => StoredSession | null,
  applySession: (payload: AuthSessionPayload) => StoredSession,
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
  currentSession: StoredSession | null,
  getStoredSession: () => StoredSession | null,
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
