import { useState } from "react";
import { ApiError, loginUser, refreshUserToken, registerUser, revokeUserToken } from "../api/authApi";
import { clearStoredSession, getStoredSession, storeSession } from "./session";

export function useAuthSession() {
  const [authSession, setAuthSession] = useState(() => getStoredSession());

  function applySession(payload) {
    const nextSession = {
      username: payload.user.username,
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
    };
    storeSession(nextSession);
    setAuthSession(nextSession);
    return nextSession;
  }

  async function login(rawUsername, rawPassword) {
    const username = rawUsername.trim();
    const password = rawPassword.trim();

    if (!username || !password) {
      throw new Error("Username and password are required");
    }

    const payload = await loginUser(username, password);
    applySession(payload);
  }

  async function register(rawUsername, rawPassword) {
    const username = rawUsername.trim();
    const password = rawPassword.trim();

    if (!username || !password) {
      throw new Error("Username and password are required");
    }

    await registerUser(username, password);
    await login(username, password);
  }

  async function refreshAccessToken() {
    const current = authSession || getStoredSession();
    if (!current?.refreshToken) {
      clearStoredSession();
      setAuthSession(null);
      throw new Error("Session expired. Please sign in again.");
    }

    try {
      const payload = await refreshUserToken(current.refreshToken);
      const nextSession = applySession(payload);
      return nextSession.accessToken;
    } catch (err) {
      clearStoredSession();
      setAuthSession(null);
      throw err;
    }
  }

  async function withAuthenticatedRequest(operation) {
    const current = authSession || getStoredSession();
    if (!current?.accessToken) {
      throw new Error("Session expired. Please sign in again.");
    }

    try {
      return await operation(current.accessToken);
    } catch (err) {
      if (!(err instanceof ApiError) || err.status !== 401 || !current.refreshToken) {
        throw err;
      }

      const refreshedAccessToken = await refreshAccessToken();
      return operation(refreshedAccessToken);
    }
  }

  async function logout() {
    const current = authSession || getStoredSession();
    if (current?.refreshToken) {
      try {
        await revokeUserToken(current.refreshToken);
      } catch {
        // Ignore revoke failures and clear local state anyway.
      }
    }

    clearStoredSession();
    setAuthSession(null);
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
