import { useEffect, useMemo, useState } from "react";
import { createTask, deleteTask, getTasks, getTasksByStatus, updateTask } from "./api";

const STATUS_LABELS = {
  todo: "Todo",
  in_progress: "In Progress",
  done: "Done",
  archived: "Archived"
};

const STATUS_ORDER = ["todo", "in_progress", "done", "archived"];

const isArchivedStatus = (status) => status === "archived";

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [showArchivedOnly, setShowArchivedOnly] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function loadTasks() {
    try {
      setLoading(true);
      setError("");
      setShowArchivedOnly(false);
      const data = await getTasks();
      setTasks(data);
    } catch (err) {
      setError(err.message || "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }

  async function loadArchivedTasks() {
    try {
      setLoading(true);
      setError("");
      setShowArchivedOnly(true);
      const data = await getTasksByStatus("archived");
      setTasks(data);
    } catch (err) {
      setError(err.message || "Failed to load archived tasks");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
  }, []);

  async function handleCreateTask(event) {
    event.preventDefault();
    if (!title.trim()) {
      setError("Title is required");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      await createTask({
        title: title.trim(),
        description: description.trim() || null,
      });
      setTitle("");
      setDescription("");
      await loadTasks();
    } catch (err) {
      setError(err.message || "Failed to create task");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStatusChange(task, newStatus) {
    try {
      setError("");
      await updateTask(task.id, { status: newStatus });
      if (isArchivedStatus(newStatus)) {
        await loadTasks();
      } else {
        await loadArchivedTasks();
      }
    } catch (err) {
      setError(err.message || "Failed to update task");
    }
  }

  async function handleDeleteTask(taskId) {
    try {
      setError("");
      await deleteTask(taskId);
      await loadTasks();
    } catch (err) {
      setError(err.message || "Failed to delete task");
    }
  }

  const groupedTasks = useMemo(() => {
    const visibleStatuses = showArchivedOnly
      ? ["archived"]
      : STATUS_ORDER.filter((status) => !isArchivedStatus(status));

    return visibleStatuses.map((status) => ({
      status,
      tasks: tasks.filter((task) => task.status === status),
    }));
  }, [showArchivedOnly, tasks]);

  return (
    <div className="page-shell">
      <header className="hero">
        <p className="hero-kicker">Task Management API</p>
        <h1>Fluxboard</h1>
        <small className="version"><v1 className="0 2"></v1></small>
        <p className="hero-subtitle">
          A live React interface for your FastAPI + SQLite task service.
        </p>
      </header>

      <section className="composer">
        <form onSubmit={handleCreateTask} className="composer-form">
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
            &nbsp;
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
                      onChange={(event) => handleStatusChange(task, event.target.value)}
                    >
                      {STATUS_ORDER.map((status) => (
                        <option key={status} value={status}>
                          {STATUS_LABELS[status]}
                        </option>
                      ))}
                    </select>
                    <button onClick={() => handleDeleteTask(task.id)}>Delete</button>
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
