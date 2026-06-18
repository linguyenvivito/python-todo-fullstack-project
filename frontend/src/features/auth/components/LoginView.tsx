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
    <div className="relative grid min-h-screen place-items-center overflow-hidden px-4 py-10 sm:px-6">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-20 top-0 h-64 w-64 rounded-full bg-primary/20 blur-3xl" />
        <div className="absolute -right-12 bottom-10 h-72 w-72 rounded-full bg-secondary/20 blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-5xl columns-1 gap-4 lg:columns-2">
        <section className="card mb-4 break-inside-avoid border border-base-200 shadow-xl">
          <div className="card-body p-6 sm:p-8">
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-primary">
              Task Management API
            </p>
            <h1 className="mt-3 text-4xl font-bold leading-tight text-base-content sm:text-5xl">
              Welcome to Fluxboard
            </h1>
            <p className="mt-3 max-w-lg text-sm text-base-content/70 sm:text-base">
              {mode === "register"
                ? "Create an account to start managing your tasks."
                : "Sign in to continue to your todo workspace."}
            </p>
            <div className="mt-4">
              <span className="badge badge-outline badge-primary badge-lg font-mono text-[11px] uppercase tracking-wide">
                FastAPI + React + daisyUI
              </span>
            </div>
          </div>
        </section>

        <section className="card mb-4 break-inside-avoid border border-base-200 shadow-xl">
          <div className="card-body p-6 sm:p-8">
            <form onSubmit={handleSubmit} className="grid gap-4">
              <label className="form-control w-full gap-1.5">
                <span className="label-text font-mono text-xs font-medium uppercase tracking-wide text-base-content/70">
                  Username
                </span>
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(event) => setLoginUsername(event.target.value)}
                  placeholder="project-owner"
                  autoComplete="username"
                  className="input input-bordered w-full"
                />
              </label>

              <label className="form-control w-full gap-1.5">
                <span className="label-text font-mono text-xs font-medium uppercase tracking-wide text-base-content/70">
                  Password
                </span>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(event) => setLoginPassword(event.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="input input-bordered w-full"
                />
              </label>

              {loginError && (
                <div className="alert alert-error">
                  <span>{loginError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loginSubmitting}
                className="btn btn-primary w-full"
              >
                {loginSubmitting ? (
                  <>
                    <span className="loading loading-spinner loading-sm" />
                    Signing in...
                  </>
                ) : mode === "register" ? (
                  "Create account"
                ) : (
                  "Sign in"
                )}
              </button>

              <button
                type="button"
                onClick={() => setMode(mode === "login" ? "register" : "login")}
                className="btn btn-ghost btn-sm text-xs"
              >
                {mode === "login" ? "Need an account? Sign up" : "Already have an account? Sign in"}
              </button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
