import { useState } from "react";
import {
  loginAndApplySession,
  registerAndLogin,
  executeWithTokenRefresh,
  logout as logoutService,
  type AuthSessionPayloadType,
} from "../services/authService";
import { clearStoredSession, getStoredSession, storeSession } from "./session";
import type { StoredSession } from "./session";
import type { AuthRequestOperation } from "../../../types";

export function useAuthSession() {
  const [authSession, setAuthSession] = useState<StoredSession | null>(() => getStoredSession());

  function applySession(payload: AuthSessionPayloadType): StoredSession {
    const nextSession: StoredSession = {
      username: payload.user.username,
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
    };
    storeSession(nextSession);
    setAuthSession(nextSession);
    return nextSession;
  }

  function clearSession(): void {
    clearStoredSession();
    setAuthSession(null);
  }

  async function login(username: string, password: string) {
    await loginAndApplySession(username, password, applySession);
  }

  async function register(username: string, password: string) {
    await registerAndLogin(username, password, applySession);
  }

  async function withAuthenticatedRequest<T>(operation: AuthRequestOperation<T>): Promise<T> {
    return executeWithTokenRefresh(authSession, getStoredSession, applySession, clearSession, operation);
  }

  async function logout() {
    await logoutService(authSession, getStoredSession, clearSession);
  }

  return {
    authUser: authSession?.username || "",
    accessToken: authSession?.accessToken || "",
    refreshToken: authSession?.refreshToken || "",
    login,
    register,
    withAuthenticatedRequest,
    logout,
  };
}
