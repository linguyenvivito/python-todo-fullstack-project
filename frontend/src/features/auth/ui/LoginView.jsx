import { useState } from "react";

export default function LoginView({ onLogin, onRegister }) {
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginSubmitting, setLoginSubmitting] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [mode, setMode] = useState("login");

  async function handleSubmit(event) {
    event.preventDefault();

    try {
      setLoginSubmitting(true);
      setLoginError("");
      if (mode === "register") {
        await onRegister(loginUsername, loginPassword);
      } else {
        await onLogin(loginUsername, loginPassword);
      }
      setLoginPassword("");
    } catch (err) {
      setLoginError(err.message || "Unable to sign in");
    } finally {
      setLoginSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-card">
        <p className="hero-kicker">Task Management API</p>
        <h1>Welcome to Fluxboard</h1>
        <p className="hero-subtitle">
          {mode === "register"
            ? "Create an account to start managing your tasks."
            : "Sign in to continue to your todo workspace."}
        </p>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Username
            <input
              type="text"
              value={loginUsername}
              onChange={(event) => setLoginUsername(event.target.value)}
              placeholder="project-owner"
              autoComplete="username"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={loginPassword}
              onChange={(event) => setLoginPassword(event.target.value)}
              placeholder="Enter password"
              autoComplete="current-password"
            />
          </label>
          {loginError && <p className="status-banner error">{loginError}</p>}
          <button type="submit" disabled={loginSubmitting}>
            {loginSubmitting ? "Please wait..." : mode === "register" ? "Create Account" : "Sign In"}
          </button>
          <button
            type="button"
            className="auth-secondary"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setLoginError("");
            }}
          >
            {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
          </button>
        </form>
      </section>
    </div>
  );
}
