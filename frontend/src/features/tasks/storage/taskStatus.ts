export const STATUS_LABELS = {
  todo: "Todo",
  in_progress: "In Progress",
  done: "Done",
  archived: "Archived",
};

export const STATUS_ORDER = ["todo", "in_progress", "done", "archived"];

export function isArchivedStatus(status) {
  return status === "archived";
}
