import { useState } from "react";
import { loginUser, registerUser } from "../api/authApi";
import { clearStoredSession, getStoredSession, storeSession } from "./session";

export function useAuthSession() {
  const [authSession, setAuthSession] = useState(() => getStoredSession());

  async function login(rawUsername, rawPassword) {
    const username = rawUsername.trim();
    const password = rawPassword.trim();

    if (!username || !password) {
      throw new Error("Username and password are required");
    }

    const payload = await loginUser(username, password);
    const nextSession = {
      username: payload.user.username,
      accessToken: payload.access_token,
    };

    storeSession(nextSession);
    setAuthSession(nextSession);
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

  function logout() {
    clearStoredSession();
    setAuthSession(null);
  }

  return {
    authUser: authSession?.username || "",
    accessToken: authSession?.accessToken || "",
    login,
    register,
    logout,
  };
}
