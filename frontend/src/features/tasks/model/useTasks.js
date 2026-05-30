import { useEffect, useMemo, useState } from "react";
import { createTask, deleteTask, getTasks, getTasksByStatus, updateTask } from "../api/tasksApi";
import { isArchivedStatus, STATUS_ORDER } from "./taskStatus";

export function useTasks(accessToken, withAuthenticatedRequest) {
  const isAuthenticated = Boolean(accessToken);
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
      const data = await withAuthenticatedRequest((token) => getTasks(token));
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
      const data = await withAuthenticatedRequest((token) => getTasksByStatus(token, "archived"));
      setTasks(data);
    } catch (err) {
      setError(err.message || "Failed to load archived tasks");
    } finally {
      setLoading(false);
    }
  }

  async function createNewTask(event) {
    event.preventDefault();
    if (!title.trim()) {
      setError("Title is required");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      await withAuthenticatedRequest((token) =>
        createTask(token, {
          title: title.trim(),
          description: description.trim() || null,
        })
      );
      setTitle("");
      setDescription("");
      await loadTasks();
    } catch (err) {
      setError(err.message || "Failed to create task");
    } finally {
      setSubmitting(false);
    }
  }

  async function changeTaskStatus(task, newStatus) {
    try {
      setError("");
      await withAuthenticatedRequest((token) => updateTask(token, task.id, { status: newStatus }));
      if (isArchivedStatus(newStatus)) {
        await loadArchivedTasks();
      } else {
        await loadTasks();
      }
    } catch (err) {
      setError(err.message || "Failed to update task");
    }
  }

  async function removeTask(taskId) {
    try {
      setError("");
      await withAuthenticatedRequest((token) => deleteTask(token, taskId));
      await loadTasks();
    } catch (err) {
      setError(err.message || "Failed to delete task");
    }
  }

  useEffect(() => {
    if (!isAuthenticated) {
      setTasks([]);
      setShowArchivedOnly(false);
      setError("");
      setTitle("");
      setDescription("");
      return;
    }

    loadTasks();
  }, [isAuthenticated, accessToken]);

  const groupedTasks = useMemo(() => {
    const visibleStatuses = showArchivedOnly
      ? ["archived"]
      : STATUS_ORDER.filter((status) => !isArchivedStatus(status));

    return visibleStatuses.map((status) => ({
      status,
      tasks: tasks.filter((task) => task.status === status),
    }));
  }, [showArchivedOnly, tasks]);

  return {
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
  };
}
