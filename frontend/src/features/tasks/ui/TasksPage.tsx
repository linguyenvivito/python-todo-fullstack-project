import { STATUS_LABELS, STATUS_ORDER } from "../storage/taskStatus";
import { useTasks } from "../storage/useTasks";

const statusCardClasses = {
  todo: "border-info/40 bg-info/10",
  in_progress: "border-warning/40 bg-warning/10",
  done: "border-success/40 bg-success/10",
  archived: "border-error/40 bg-error/10",
};

export default function TasksPage({
  authUser,
  accessToken,
  withAuthenticatedRequest,
}) {
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
  } = useTasks(accessToken, withAuthenticatedRequest);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="card border border-base-200 shadow-xl">
        <div className="card-body p-6 sm:p-8">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          Task Management API
        </p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight text-base-content sm:text-5xl">Fluxboard</h1>
        <small className="mt-1 block font-mono text-xs text-base-content/60">v0.6</small>
        <p className="mt-3 max-w-3xl text-sm text-base-content/70 sm:text-base">
          A live React interface for your FastAPI + PostgreSQL task service.
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
        <form onSubmit={createNewTask} className="grid gap-3">
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Ship REST API docs"
            maxLength={100}
            className="input input-bordered w-full"
          />
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Describe what done looks like..."
            maxLength={500}
            rows={3}
            className="textarea textarea-bordered w-full"
          />

          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={submitting}
              className="btn btn-primary btn-sm"
            >
              {submitting ? "Adding..." : "Add Task"}
            </button>

            <button
              type="button"
              onClick={loadTasks}
              disabled={loading}
              className="btn btn-outline btn-sm"
            >
              Refresh
            </button>

            <button
              type="button"
              onClick={loadArchivedTasks}
              disabled={loading}
              className="btn btn-outline btn-sm"
            >
              Load Archived
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
          <span>Loading tasks...</span>
        </div>
      )}

      <main className="mt-5 columns-1 gap-4 lg:columns-3">
        {groupedTasks.map((column) => (
          <section key={column.status} className="card mb-4 break-inside-avoid border border-base-200 shadow-xl overflow-hidden">
            <div className="flex items-center justify-between border-b border-base-200 bg-base-200 px-4 py-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-base-content/80">
                {STATUS_LABELS[column.status]}
              </h2>
              <span className="badge badge-outline badge-primary font-mono text-xs">
                {column.tasks.length}
              </span>
            </div>

            <div className="columns-1 gap-3 p-3 sm:columns-2 lg:columns-1">
              {column.tasks.map((task) => (
                <article
                  key={task.id}
                  className={`mb-3 break-inside-avoid rounded-2xl border p-3 shadow-sm transition ${
                    statusCardClasses[task.status] || "border-base-300"
                  }`}
                >
                  <h3 className="text-base font-semibold text-base-content">{task.title}</h3>
                  <p className="mt-2 text-sm text-base-content/70">{task.description || "No description"}</p>

                  <div className="mt-3 flex items-center gap-2">
                    <select
                      value={task.status}
                      onChange={(event) => changeTaskStatus(task, event.target.value)}
                      className="select select-bordered select-sm w-full"
                    >
                      {STATUS_ORDER.map((status) => (
                        <option key={status} value={status}>
                          {STATUS_LABELS[status]}
                        </option>
                      ))}
                    </select>

                    <button
                      type="button"
                      onClick={() => removeTask(task.id)}
                      className="btn btn-error btn-outline btn-sm"
                    >
                      Delete
                    </button>
                  </div>
                </article>
              ))}

              {column.tasks.length === 0 && (
                <p className="rounded-xl border border-dashed border-base-300 px-3 py-3 font-mono text-xs uppercase tracking-wide text-base-content/60">
                  No tasks yet
                </p>
              )}
            </div>
          </section>
        ))}
      </main>
    </div>
  );
}
