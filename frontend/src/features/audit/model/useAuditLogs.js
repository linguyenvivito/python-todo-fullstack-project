import { useCallback, useEffect, useMemo, useState } from "react";
import { getAuditLogs } from "../api/auditApi";

const DEFAULT_LIMIT = 25;

function toEpochSeconds(value) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return Math.floor(date.getTime() / 1000);
}

export function useAuditLogs(accessToken, withAuthenticatedRequest) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [action, setAction] = useState("");
  const [success, setSuccess] = useState("all");
  const [occurredFrom, setOccurredFrom] = useState("");
  const [occurredTo, setOccurredTo] = useState("");
  const [offset, setOffset] = useState(0);

  const limit = DEFAULT_LIMIT;

  const query = useMemo(() => {
    const parsedSuccess = success === "all" ? null : success === "success";
    return {
      action: action.trim() || null,
      success: parsedSuccess,
      occurred_from: toEpochSeconds(occurredFrom),
      occurred_to: toEpochSeconds(occurredTo),
      limit,
      offset,
    };
  }, [action, success, occurredFrom, occurredTo, limit, offset]);

  const loadLogs = useCallback(async () => {
    if (!accessToken) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const payload = await withAuthenticatedRequest((token) => getAuditLogs(token, query));
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

  function applyFilters(event) {
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
