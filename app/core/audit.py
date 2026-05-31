import json
import time
from functools import lru_cache
from typing import Any, Mapping, Optional, cast

from starlette.requests import Request

try:
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    dict_row = None

from app.core.database import get_connection, init_database
from app.core.models import AuditLog


class AuditRepository:
    def __init__(self) -> None:
        init_database()

    @staticmethod
    def _row_to_audit_log(row: Any) -> AuditLog:
        return AuditLog(
            id=row["id"],
            occurred_at=row["occurred_at"],
            actor_user_id=row["actor_user_id"],
            action=row["action"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            success=bool(row["success"]),
            http_method=row["http_method"],
            path=row["path"],
            status_code=row["status_code"],
            client_ip=row["client_ip"],
            user_agent=row["user_agent"],
            request_id=row["request_id"],
            details_json=row["details_json"],
        )

    def create(
        self,
        *,
        occurred_at: int,
        actor_user_id: Optional[int],
        action: str,
        resource_type: Optional[str],
        resource_id: Optional[str],
        success: bool,
        http_method: Optional[str],
        path: Optional[str],
        status_code: Optional[int],
        client_ip: Optional[str],
        user_agent: Optional[str],
        request_id: Optional[str],
        details_json: Optional[str],
    ) -> AuditLog:
        with get_connection() as connection:
            if dict_row is None:
                raise RuntimeError("PostgreSQL mode requires psycopg to be installed.")

            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor(row_factory=dict_row)
            try:
                cursor.execute(
                    """
                    INSERT INTO audit_logs (
                        occurred_at,
                        actor_user_id,
                        action,
                        resource_type,
                        resource_id,
                        success,
                        http_method,
                        path,
                        status_code,
                        client_ip,
                        user_agent,
                        request_id,
                        details_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING
                        id,
                        occurred_at,
                        actor_user_id,
                        action,
                        resource_type,
                        resource_id,
                        success,
                        http_method,
                        path,
                        status_code,
                        client_ip,
                        user_agent,
                        request_id,
                        details_json
                    """,
                    (
                        occurred_at,
                        actor_user_id,
                        action,
                        resource_type,
                        resource_id,
                        success,
                        http_method,
                        path,
                        status_code,
                        client_ip,
                        user_agent,
                        request_id,
                        details_json,
                    ),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
            connection.commit()

        if row is None:
            raise RuntimeError("Failed to create audit log")
        return self._row_to_audit_log(row)

    @staticmethod
    def _build_filters(
        *,
        action: Optional[str],
        success: Optional[bool],
        actor_user_id: Optional[int],
        occurred_from: Optional[int],
        occurred_to: Optional[int],
        placeholder: str,
    ) -> tuple[str, list[Any]]:
        conditions: list[str] = []
        params: list[Any] = []

        if action:
            conditions.append(f"LOWER(action) LIKE LOWER({placeholder})")
            params.append(f"%{action}%")
        if success is not None:
            conditions.append(f"success = {placeholder}")
            params.append(success)
        if actor_user_id is not None:
            conditions.append(f"actor_user_id = {placeholder}")
            params.append(actor_user_id)
        if occurred_from is not None:
            conditions.append(f"occurred_at >= {placeholder}")
            params.append(occurred_from)
        if occurred_to is not None:
            conditions.append(f"occurred_at <= {placeholder}")
            params.append(occurred_to)

        if not conditions:
            return "", params
        return f" WHERE {' AND '.join(conditions)}", params

    def list(
        self,
        *,
        action: Optional[str],
        success: Optional[bool],
        actor_user_id: Optional[int],
        occurred_from: Optional[int],
        occurred_to: Optional[int],
        limit: int,
        offset: int,
    ) -> list[AuditLog]:
        with get_connection() as connection:
            if dict_row is None:
                raise RuntimeError("PostgreSQL mode requires psycopg to be installed.")

            where_clause, params = self._build_filters(
                action=action,
                success=success,
                actor_user_id=actor_user_id,
                occurred_from=occurred_from,
                occurred_to=occurred_to,
                placeholder="%s",
            )
            query = f"""
                SELECT
                    id,
                    occurred_at,
                    actor_user_id,
                    action,
                    resource_type,
                    resource_id,
                    success,
                    http_method,
                    path,
                    status_code,
                    client_ip,
                    user_agent,
                    request_id,
                    details_json
                FROM audit_logs
                {where_clause}
                ORDER BY id DESC
                LIMIT %s
                OFFSET %s
            """
            typed_query = cast(Any, query)

            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor(row_factory=dict_row)
            try:
                cursor.execute(typed_query, (*params, limit, offset))
                rows = cursor.fetchall()
            finally:
                cursor.close()

        return [self._row_to_audit_log(row) for row in rows]

    def count(
        self,
        *,
        action: Optional[str],
        success: Optional[bool],
        actor_user_id: Optional[int],
        occurred_from: Optional[int],
        occurred_to: Optional[int],
    ) -> int:
        with get_connection() as connection:
            where_clause, params = self._build_filters(
                action=action,
                success=success,
                actor_user_id=actor_user_id,
                occurred_from=occurred_from,
                occurred_to=occurred_to,
                placeholder="%s",
            )
            count_query = cast(
                Any,
                f"""
                SELECT COUNT(*)
                FROM audit_logs
                {where_clause}
                """,
            )
            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor()
            try:
                cursor.execute(count_query, tuple(params))
                row = cursor.fetchone()
            finally:
                cursor.close()

        return int(row[0] if row else 0)


class AuditService:
    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    @staticmethod
    def _clean_string(value: Any, max_length: int = 512) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return text[:max_length]

    @staticmethod
    def _sanitize_details(details: Optional[Mapping[str, Any]]) -> Optional[str]:
        if not details:
            return None

        redacted_terms = ("password", "token", "secret", "authorization", "cookie")
        cleaned: dict[str, Any] = {}
        for key, value in details.items():
            normalized_key = str(key).strip().lower()
            if any(term in normalized_key for term in redacted_terms):
                cleaned[normalized_key] = "[REDACTED]"
                continue

            if isinstance(value, (str, int, float, bool)) or value is None:
                if isinstance(value, str):
                    cleaned[normalized_key] = value[:512]
                else:
                    cleaned[normalized_key] = value
                continue

            cleaned[normalized_key] = str(value)[:512]

        if not cleaned:
            return None
        return json.dumps(cleaned, ensure_ascii=True, separators=(",", ":"))

    def record_event(
        self,
        *,
        action: str,
        success: bool,
        request: Optional[Request] = None,
        actor_user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Mapping[str, Any]] = None,
    ) -> AuditLog:
        client_ip = None
        user_agent = None
        http_method = None
        path = None
        request_id = None

        if request is not None:
            http_method = self._clean_string(request.method, max_length=16)
            path = self._clean_string(str(request.url.path), max_length=512)
            request_id = self._clean_string(request.headers.get("x-request-id"), max_length=128)
            user_agent = self._clean_string(request.headers.get("user-agent"), max_length=512)
            client_ip = self._clean_string(
                request.client.host if request.client else None,
                max_length=64,
            )

        return self._repository.create(
            occurred_at=int(time.time()),
            actor_user_id=actor_user_id,
            action=self._clean_string(action, max_length=128) or "unknown.action",
            resource_type=self._clean_string(resource_type, max_length=64),
            resource_id=self._clean_string(resource_id, max_length=128),
            success=success,
            http_method=http_method,
            path=path,
            status_code=status_code,
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request_id,
            details_json=self._sanitize_details(details),
        )

    def list_events(
        self,
        *,
        action: Optional[str],
        success: Optional[bool],
        actor_user_id: Optional[int],
        occurred_from: Optional[int],
        occurred_to: Optional[int],
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        cleaned_action = self._clean_string(action, max_length=128)
        items = self._repository.list(
            action=cleaned_action,
            success=success,
            actor_user_id=actor_user_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
            limit=limit,
            offset=offset,
        )
        total = self._repository.count(
            action=cleaned_action,
            success=success,
            actor_user_id=actor_user_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
        )
        return items, total


@lru_cache(maxsize=1)
def _get_audit_service() -> AuditService:
    return AuditService(AuditRepository())


class _LazyAuditService:
    def record_event(self, *args, **kwargs):
        return _get_audit_service().record_event(*args, **kwargs)

    def list_events(self, *args, **kwargs):
        return _get_audit_service().list_events(*args, **kwargs)


audit_service = _LazyAuditService()
