import { getAuditLogs } from "../api/auditApi";
import type { AuditLogEntry, AuditLogQuery, WithAuthenticatedRequest } from "../../../types";

export const DEFAULT_LIMIT = 25;

/**
 * Convert a datetime-local string or timestamp to epoch seconds.
 * Returns null if the value is empty or invalid.
 */
export function toEpochSeconds(value: string | null | undefined): number | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return Math.floor(date.getTime() / 1000);
}

/**
 * Build a typed AuditLogQuery object from filter values.
 */
export function buildAuditQuery(
  action: string,
  success: string,
  occurredFrom: string,
  occurredTo: string,
  limit: number,
  offset: number
): AuditLogQuery {
  const parsedSuccess = success === "all" ? null : success === "success";
  return {
    action: action.trim() || null,
    success: parsedSuccess,
    occurred_from: toEpochSeconds(occurredFrom),
    occurred_to: toEpochSeconds(occurredTo),
    limit,
    offset,
  };
}

/**
 * Fetch audit logs for the given query and authenticated request context.
 */
export async function fetchAuditLogs(
  withAuthenticatedRequest: WithAuthenticatedRequest,
  query: AuditLogQuery
): Promise<{ items: AuditLogEntry[]; total: number }> {
  return withAuthenticatedRequest((token) => getAuditLogs(token, query));
}
