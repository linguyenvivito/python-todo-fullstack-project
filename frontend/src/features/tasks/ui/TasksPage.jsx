import { STATUS_LABELS, STATUS_ORDER } from "../model/taskStatus";
import { useTasks } from "../model/useTasks";

export default function TasksPage({ authUser, accessToken, onLogout }) {
  const {
    title,
    setTitle,
    description,
    setDescription,
    loading,
    submitting,
    error,
    groupedTasks,
    loadTasks,
    loadArchivedTasks,
    createNewTask,
    changeTaskStatus,
    removeTask,
  } = useTasks(accessToken);

  return (
    <div className="page-shell">
      <header className="hero">
        <p className="hero-kicker">Task Management API</p>
        <h1>Fluxboard</h1>
        <small className="version">v0.3</small>
        <p className="hero-subtitle">
          A live React interface for your FastAPI + PostgreSQL task service.
        </p>
        <div className="hero-meta">
          <span>Signed in as {authUser}</span>
          <button type="button" onClick={onLogout}>Logout</button>
        </div>
      </header>

      <section className="composer">
        <form onSubmit={createNewTask} className="composer-form">
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Ship REST API docs"
            maxLength={100}
          />
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Describe what done looks like..."
            maxLength={500}
            rows={3}
          />
          <div className="form-actions">
            <button type="submit" disabled={submitting}>
              {submitting ? "Adding..." : "Add Task"}
            </button>
            <button type="button" onClick={loadTasks} disabled={loading}>
              Refresh
            </button>
            <button type="button" onClick={loadArchivedTasks} disabled={loading}>
              Load Archived
            </button>
          </div>
        </form>
      </section>

      {error && <p className="status-banner error">{error}</p>}
      {loading && <p className="status-banner">Loading tasks...</p>}

      <main className="board">
        {groupedTasks.map((column) => (
          <section key={column.status} className="column">
            <div className="column-head">
              <h2>{STATUS_LABELS[column.status]}</h2>
              <span>{column.tasks.length}</span>
            </div>
            <div className="column-body">
              {column.tasks.map((task) => (
                <article key={task.id} className={`task-card ${task.status}`}>
                  <h3>{task.title}</h3>
                  <p>{task.description || "No description"}</p>
                  <div className="card-actions">
                    <select
                      value={task.status}
                      onChange={(event) => changeTaskStatus(task, event.target.value)}
                    >
                      {STATUS_ORDER.map((status) => (
                        <option key={status} value={status}>
                          {STATUS_LABELS[status]}
                        </option>
                      ))}
                    </select>
                    <button onClick={() => removeTask(task.id)}>Delete</button>
                  </div>
                </article>
              ))}
              {column.tasks.length === 0 && <p className="empty-state">No tasks yet</p>}
            </div>
          </section>
        ))}
      </main>
    </div>
  );
}
