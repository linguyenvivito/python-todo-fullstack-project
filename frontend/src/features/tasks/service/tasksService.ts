import { createTask, deleteTask, getTasks, getTasksByStatus, updateTask } from "../api/tasksApi";
import type { Task, TaskCreatePayload, TaskUpdatePayload, WithAuthenticatedRequest } from "../../../types";
import { isArchivedStatus, STATUS_ORDER } from "../storage/taskStatus";

export const DEFAULT_TASK_LIMIT = 25;

/**
 * Group tasks by status, filtering archived tasks if needed.
 */
export function groupTasksByStatus(
  tasks: Task[],
  showArchivedOnly: boolean
): Array<{ status: string; tasks: Task[] }> {
  const visibleStatuses = showArchivedOnly
    ? ["archived"]
    : STATUS_ORDER.filter((status) => !isArchivedStatus(status));

  return visibleStatuses.map((status) => ({
    status,
    tasks: tasks.filter((task) => task.status === status),
  }));
}

/**
 * Fetch tasks, optionally filtered by status (archived or all).
 */
export async function fetchTasks(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  showArchived: boolean = false
): Promise<Task[]> {
  if (showArchived) {
    return withAuthenticatedRequest((token) => getTasksByStatus(token, "archived"));
  }
  return withAuthenticatedRequest((token) => getTasks(token));
}

/**
 * Create a new task with validation.
 */
export async function createNewTask(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  title: string,
  description: string
): Promise<void> {
  const trimmedTitle = title.trim();
  if (!trimmedTitle) {
    throw new Error("Title is required");
  }

  await withAuthenticatedRequest((token) =>
    createTask(token, {
      title: trimmedTitle,
      description: description.trim() || null,
    })
  );
}

/**
 * Update task status and return updated task list.
 */
export async function updateTaskStatus(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  task: Task,
  newStatus: Task["status"]
): Promise<Task[]> {
  await withAuthenticatedRequest((token) =>
    updateTask(token, task.id, { status: newStatus })
  );
  return fetchTasks(withAuthenticatedRequest, isArchivedStatus(newStatus));
}

/**
 * Delete a task by ID.
 */
export async function deleteTaskById(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  taskId: number
): Promise<void> {
  await withAuthenticatedRequest((token) => deleteTask(token, taskId));
}
