import { useState } from "react";

export default function LoginView({ onLogin }) {
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginSubmitting, setLoginSubmitting] = useState(false);
  const [loginError, setLoginError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    try {
      setLoginSubmitting(true);
      setLoginError("");
      await onLogin(loginUsername, loginPassword);
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
        <p className="hero-subtitle">Sign in to continue to your todo workspace.</p>
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
            {loginSubmitting ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </section>
    </div>
  );
}
