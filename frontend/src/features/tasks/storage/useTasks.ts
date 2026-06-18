import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  groupTasksByStatus,
  fetchTasks,
  createNewTask as createTaskService,
  updateTaskStatus as updateTaskStatusService,
  deleteTaskById,
} from "../service/tasksService";
import type { Task, WithAuthenticatedRequest } from "../../../types";

export function useTasks(accessToken: string, withAuthenticatedRequest: WithAuthenticatedRequest) {
  const isAuthenticated = Boolean(accessToken);
  const [tasks, setTasks] = useState<Task[]>([]);
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
      const data = await fetchTasks(withAuthenticatedRequest, false);
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
      const data = await fetchTasks(withAuthenticatedRequest, true);
      setTasks(data);
    } catch (err) {
      setError(err.message || "Failed to load archived tasks");
    } finally {
      setLoading(false);
    }
  }

  async function createNewTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError("");
      await createTaskService(withAuthenticatedRequest, title, description);
      setTitle("");
      setDescription("");
      await loadTasks();
    } catch (err) {
      setError(err.message || "Failed to create task");
    } finally {
      setSubmitting(false);
    }
  }

  async function changeTaskStatus(task: Task, newStatus: Task["status"]) {
    try {
      setError("");
      const updatedTasks = await updateTaskStatusService(withAuthenticatedRequest, task, newStatus);
      setTasks(updatedTasks);
    } catch (err) {
      setError(err.message || "Failed to update task");
    }
  }

  async function removeTask(taskId: number) {
    try {
      setError("");
      await deleteTaskById(withAuthenticatedRequest, taskId);
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
    return groupTasksByStatus(tasks, showArchivedOnly);
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
