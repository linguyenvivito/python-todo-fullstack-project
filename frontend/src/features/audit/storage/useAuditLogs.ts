import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { DEFAULT_LIMIT, buildAuditQuery, fetchAuditLogs } from "../service/auditService";
import type { AuditLogEntry, AuditLogQuery, WithAuthenticatedRequest } from "../../../types";

export function useAuditLogs(accessToken: string, withAuthenticatedRequest: WithAuthenticatedRequest) {
  const [items, setItems] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [action, setAction] = useState("");
  const [success, setSuccess] = useState("all");
  const [occurredFrom, setOccurredFrom] = useState("");
  const [occurredTo, setOccurredTo] = useState("");
  const [offset, setOffset] = useState(0);

  const limit = DEFAULT_LIMIT;

  const query = useMemo<AuditLogQuery>(
    () => buildAuditQuery(action, success, occurredFrom, occurredTo, limit, offset),
    [action, success, occurredFrom, occurredTo, limit, offset]
  );

  const loadLogs = useCallback(async () => {
    if (!accessToken) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const payload = await fetchAuditLogs(withAuthenticatedRequest, query);
      setItems(payload.items || []);
      setTotal(payload.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, [accessToken, query, withAuthenticatedRequest]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setOffset(0);
    loadLogs();
  }

  function clearFilters() {
    setAction("");
    setSuccess("all");
    setOccurredFrom("");
    setOccurredTo("");
    setOffset(0);
  }

  function goNext() {
    if (offset + limit < total) {
      setOffset((current) => current + limit);
    }
  }

  function goPrevious() {
    if (offset > 0) {
      setOffset((current) => Math.max(0, current - limit));
    }
  }

  return {
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
    reload: loadLogs,
    goNext,
    goPrevious,
  };
}
