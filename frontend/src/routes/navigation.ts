/**
 * Application routing configuration and utilities.
 */

export type PageId = "tasks" | "user" | "audit" | "email" | "roles";

export interface MenuItem {
  id: PageId;
  label: string;
  path: string;
}

export const MENU_ITEMS: MenuItem[] = [
  { id: "tasks", label: "Tasks", path: "/task" },
  { id: "user", label: "User", path: "/user" },
  { id: "audit", label: "Audit Logs", path: "/audit" },
  { id: "email", label: "Email", path: "/email" },
  { id: "roles", label: "Roles", path: "/role" },
];

const PATH_TO_PAGE: Record<string, PageId> = {
  "/task": "tasks",
  "/tasks": "tasks",
  "/user": "user",
  "/users": "user",
  "/audit": "audit",
  "/email": "email",
  "/role": "roles",
  "/roles": "roles",
};

const PAGE_TO_PATH: Record<PageId, string> = {
  tasks: "/task",
  user: "/user",
  audit: "/audit",
  email: "/email",
  roles: "/role",
};

/**
 * Get the page ID from the current pathname.
 */
export function getPageFromPath(pathname: string): PageId {
  return PATH_TO_PAGE[pathname] || "tasks";
}

/**
 * Get the path for a given page ID.
 */
export function getPathFromPage(page: PageId): string {
  return PAGE_TO_PATH[page] || PAGE_TO_PATH.tasks;
}
