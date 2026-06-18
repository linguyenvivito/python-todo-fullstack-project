import { useAuditLogs } from "../storage/useAuditLogs";

function formatTime(epochSeconds) {
  if (!epochSeconds) {
    return "-";
  }
  return new Date(epochSeconds * 1000).toLocaleString();
}

export default function AuditLogsPage({
  authUser,
  accessToken,
  withAuthenticatedRequest,
}) {
  const {
    items,
    total,
    limit,
    offset,
    loading,
    error,
    action,
    setAction,
    success,
    setSuccess,
    occurredFrom,
    setOccurredFrom,
    occurredTo,
    setOccurredTo,
    applyFilters,
    clearFilters,
    reload,
    goNext,
    goPrevious,
  } = useAuditLogs(accessToken, withAuthenticatedRequest);

  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="card border border-base-200 shadow-xl">
        <div className="card-body p-6 sm:p-8">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-primary">
            Task Management API
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-base-content sm:text-5xl">Audit Console</h1>
          <small className="mt-1 block font-mono text-xs text-base-content/60">v0.6</small>
          <p className="mt-3 max-w-3xl text-sm text-base-content/70 sm:text-base">
            Trace security and business events with immutable server-side audit records.
          </p>

          <div className="mt-5">
            <span className="font-mono text-xs uppercase tracking-wide text-base-content/70">
              Signed in as {authUser}
            </span>
          </div>
        </div>
      </header>

      <section className="card mt-4 border border-base-200 shadow-xl">
        <div className="card-body p-4 sm:p-5">
          <form className="grid gap-3 md:grid-cols-2 xl:grid-cols-4" onSubmit={applyFilters}>
            <input
              type="text"
              value={action}
              onChange={(event) => setAction(event.target.value)}
              placeholder="Action contains (example: auth.login)"
              className="input input-bordered w-full"
            />

            <select
              value={success}
              onChange={(event) => setSuccess(event.target.value)}
              className="select select-bordered w-full"
            >
              <option value="all">Any result</option>
              <option value="success">Success only</option>
              <option value="failure">Failure only</option>
            </select>

            <label className="form-control w-full gap-1">
              <span className="label-text font-mono text-xs uppercase tracking-wide text-base-content/70">From</span>
              <input
                type="datetime-local"
                value={occurredFrom}
                onChange={(event) => setOccurredFrom(event.target.value)}
                className="input input-bordered w-full"
              />
            </label>

            <label className="form-control w-full gap-1">
              <span className="label-text font-mono text-xs uppercase tracking-wide text-base-content/70">To</span>
              <input
                type="datetime-local"
                value={occurredTo}
                onChange={(event) => setOccurredTo(event.target.value)}
                className="input input-bordered w-full"
              />
            </label>

            <div className="md:col-span-2 xl:col-span-4 flex flex-wrap gap-2">
              <button
                type="submit"
                className="btn btn-primary btn-sm"
              >
                Apply
              </button>

              <button
                type="button"
                onClick={clearFilters}
                className="btn btn-outline btn-sm"
              >
                Clear
              </button>

              <button
                type="button"
                onClick={reload}
                className="btn btn-outline btn-sm"
              >
                Refresh
              </button>
            </div>
          </form>
        </div>
      </section>

      {error && (
        <div className="alert alert-error mt-4">
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="alert alert-warning mt-4">
          <span>Loading audit logs...</span>
        </div>
      )}

      <section className="card mt-4 border border-base-200 shadow-xl overflow-hidden">
        <div className="flex flex-col gap-2 border-b border-base-200 bg-base-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-mono text-xs uppercase tracking-wide text-base-content/70">
            Showing {from}-{to} of {total}
          </p>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={goPrevious}
              disabled={offset === 0 || loading}
              className="btn btn-outline btn-xs"
            >
              Prev
            </button>

            <button
              type="button"
              onClick={goNext}
              disabled={loading || offset + limit >= total}
              className="btn btn-outline btn-xs"
            >
              Next
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table table-zebra table-pin-rows w-full min-w-[980px]">
            <thead>
              <tr>
                <th className="font-mono text-[11px] uppercase tracking-wide">Time</th>
                <th className="font-mono text-[11px] uppercase tracking-wide">Action</th>
                <th className="font-mono text-[11px] uppercase tracking-wide">Result</th>
                <th className="font-mono text-[11px] uppercase tracking-wide">User</th>
                <th className="font-mono text-[11px] uppercase tracking-wide">Status</th>
                <th className="font-mono text-[11px] uppercase tracking-wide">Path</th>
                <th className="font-mono text-[11px] uppercase tracking-wide">Details</th>
              </tr>
            </thead>
            <tbody>
              {items.map((entry) => (
                <tr key={entry.id}>
                  <td className="font-mono text-xs text-base-content/70">{formatTime(entry.occurred_at)}</td>
                  <td className="font-mono text-xs text-base-content">{entry.action}</td>
                  <td>
                    <span className={`badge badge-outline badge-sm ${entry.success ? "badge-success" : "badge-error"}`}>
                      {entry.success ? "success" : "failure"}
                    </span>
                  </td>
                  <td className="font-mono text-xs text-base-content">{entry.actor_user_id || "anonymous"}</td>
                  <td className="text-sm text-base-content">{entry.status_code || "-"}</td>
                  <td className="max-w-[240px] break-all font-mono text-xs text-base-content/80">{entry.path || "-"}</td>
                  <td className="max-w-[360px]">
                    <div className="max-h-28 overflow-auto rounded-lg border border-base-300 bg-base-200 px-2 py-1 font-mono text-xs text-base-content">
                      {entry.details ? JSON.stringify(entry.details, null, 2) : "-"}
                    </div>
                  </td>
                </tr>
              ))}

              {items.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="py-8 text-center">
                    <span className="text-sm text-base-content/70">No audit events match your filters.</span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
