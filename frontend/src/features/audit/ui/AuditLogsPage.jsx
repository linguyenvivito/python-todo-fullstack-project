import { useAuditLogs } from "../model/useAuditLogs";

function formatTime(epochSeconds) {
  if (!epochSeconds) {
    return "-";
  }
  return new Date(epochSeconds * 1000).toLocaleString();
}

export default function AuditLogsPage({ authUser, accessToken, withAuthenticatedRequest, onShowTasks, onLogout }) {
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
    <div className="page-shell">
      <header className="hero">
        <p className="hero-kicker">Task Management API</p>
        <h1>Audit Console</h1>
        <small className="version">v0.4</small>
        <p className="hero-subtitle">
          Trace security and business events with immutable server-side audit records.
        </p>
        <div className="hero-meta hero-meta-wrap">
          <span>Signed in as {authUser}</span>
          <div className="hero-actions">
            <button type="button" onClick={onShowTasks}>Tasks</button>
            <button type="button" onClick={onLogout}>Logout</button>
          </div>
        </div>
      </header>

      <section className="audit-filters">
        <form className="audit-filter-form" onSubmit={applyFilters}>
          <input
            type="text"
            value={action}
            onChange={(event) => setAction(event.target.value)}
            placeholder="Action contains (example: auth.login)"
          />
          <select value={success} onChange={(event) => setSuccess(event.target.value)}>
            <option value="all">Any result</option>
            <option value="success">Success only</option>
            <option value="failure">Failure only</option>
          </select>
          <label>
            From
            <input
              type="datetime-local"
              value={occurredFrom}
              onChange={(event) => setOccurredFrom(event.target.value)}
            />
          </label>
          <label>
            To
            <input
              type="datetime-local"
              value={occurredTo}
              onChange={(event) => setOccurredTo(event.target.value)}
            />
          </label>
          <div className="form-actions">
            <button type="submit">Apply</button>
            <button type="button" onClick={clearFilters}>Clear</button>
            <button type="button" onClick={reload}>Refresh</button>
          </div>
        </form>
      </section>

      {error && <p className="status-banner error">{error}</p>}
      {loading && <p className="status-banner">Loading audit logs...</p>}

      <section className="audit-table-wrap">
        <div className="audit-table-meta">
          <p>
            Showing {from}-{to} of {total}
          </p>
          <div className="audit-pager">
            <button type="button" onClick={goPrevious} disabled={offset === 0 || loading}>Prev</button>
            <button
              type="button"
              onClick={goNext}
              disabled={loading || offset + limit >= total}
            >
              Next
            </button>
          </div>
        </div>

        <div className="audit-table-scroll">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Action</th>
                <th>Result</th>
                <th>User</th>
                <th>Status</th>
                <th>Path</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {items.map((entry) => (
                <tr key={entry.id}>
                  <td>{formatTime(entry.occurred_at)}</td>
                  <td>{entry.action}</td>
                  <td>
                    <span className={entry.success ? "tag-success" : "tag-failure"}>
                      {entry.success ? "success" : "failure"}
                    </span>
                  </td>
                  <td>{entry.actor_user_id || "anonymous"}</td>
                  <td>{entry.status_code || "-"}</td>
                  <td>{entry.path || "-"}</td>
                  <td className="audit-details">{entry.details ? JSON.stringify(entry.details) : "-"}</td>
                </tr>
              ))}
              {items.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="empty-state">No audit events match your filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
