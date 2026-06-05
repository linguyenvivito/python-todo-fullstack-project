export default function UserPage({ authUser }) {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="card border border-base-200 bg-base-100 shadow-xl">
        <div className="card-body p-6 sm:p-8">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-primary">
            Task Management API
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-base-content sm:text-5xl">User Console</h1>
          <small className="mt-1 block font-mono text-xs text-base-content/60">v0.6</small>
          <p className="mt-3 max-w-3xl text-sm text-base-content/70 sm:text-base">
            View basic account information for the authenticated user.
          </p>

          <div className="mt-5 rounded-2xl border border-base-300 bg-base-200 p-4">
            <p className="font-mono text-[11px] uppercase tracking-wide text-base-content/70">Current user</p>
            <p className="mt-1 text-lg font-semibold text-base-content">{authUser}</p>
          </div>
        </div>
      </header>
    </div>
  );
}
