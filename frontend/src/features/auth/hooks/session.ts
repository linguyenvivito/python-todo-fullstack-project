import type { StoredSession } from "../../../types";

export const AUTH_SESSION_KEY = "fluxboard.auth.session";

export function getStoredSession(): StoredSession | null {
  const rawSession = sessionStorage.getItem(AUTH_SESSION_KEY);
  if (!rawSession) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawSession);
    if (!parsed?.username || !parsed?.accessToken || !parsed?.refreshToken) {
      return null;
    }
    return parsed as StoredSession;
  } catch {
    return null;
  }
}

export function storeSession(authSession: StoredSession) {
  sessionStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(authSession));
}

export function clearStoredSession() {
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}
