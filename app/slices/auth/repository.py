from dataclasses import dataclass
from typing import Any, Optional, cast

try:
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    dict_row = None

from app.core.database import get_connection, init_database
from app.core.models import User


class UserRepository:
    def __init__(self) -> None:
        init_database()

    @staticmethod
    def _row_to_user(row: Any) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
        )

    def create(self, username: str, password_hash: str) -> User:
        with get_connection() as connection:
            if dict_row is None:
                raise RuntimeError("PostgreSQL mode requires psycopg to be installed.")

            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor(row_factory=dict_row)
            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s)
                    RETURNING id, username, password_hash
                    """,
                    (username, password_hash),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
            connection.commit()

        if row is None:
            raise RuntimeError("Failed to create user")
        return self._row_to_user(row)

    def get_by_username(self, username: str) -> Optional[User]:
        with get_connection() as connection:
            if dict_row is None:
                raise RuntimeError("PostgreSQL mode requires psycopg to be installed.")

            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor(row_factory=dict_row)
            try:
                cursor.execute(
                    """
                    SELECT id, username, password_hash
                    FROM users
                    WHERE username = %s
                    """,
                    (username,),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()

        if row is None:
            return None
        return self._row_to_user(row)

    def get_by_id(self, user_id: int) -> Optional[User]:
        with get_connection() as connection:
            if dict_row is None:
                raise RuntimeError("PostgreSQL mode requires psycopg to be installed.")

            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor(row_factory=dict_row)
            try:
                cursor.execute(
                    """
                    SELECT id, username, password_hash
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()

        if row is None:
            return None
        return self._row_to_user(row)


@dataclass
class RefreshTokenRecord:
    jti: str
    user_id: int
    expires_at: int
    revoked_at: Optional[int]
    replaced_by_jti: Optional[str]


class RefreshTokenRepository:
    def __init__(self) -> None:
        init_database()

    @staticmethod
    def _row_to_record(row: Any) -> RefreshTokenRecord:
        return RefreshTokenRecord(
            jti=row["jti"],
            user_id=row["user_id"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
            replaced_by_jti=row["replaced_by_jti"],
        )

    def store(self, jti: str, user_id: int, expires_at: int) -> None:
        with get_connection() as connection:
            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO refresh_tokens (jti, user_id, expires_at, revoked_at, replaced_by_jti)
                    VALUES (%s, %s, %s, NULL, NULL)
                    """,
                    (jti, user_id, expires_at),
                )
            finally:
                cursor.close()
            connection.commit()

    def get(self, jti: str) -> Optional[RefreshTokenRecord]:
        with get_connection() as connection:
            if dict_row is None:
                raise RuntimeError("PostgreSQL mode requires psycopg to be installed.")

            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor(row_factory=dict_row)
            try:
                cursor.execute(
                    """
                    SELECT jti, user_id, expires_at, revoked_at, replaced_by_jti
                    FROM refresh_tokens
                    WHERE jti = %s
                    """,
                    (jti,),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()

        if row is None:
            return None
        return self._row_to_record(row)

    def revoke(self, jti: str, revoked_at: int, replaced_by_jti: Optional[str] = None) -> None:
        with get_connection() as connection:
            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE refresh_tokens
                    SET revoked_at = COALESCE(revoked_at, %s),
                        replaced_by_jti = COALESCE(replaced_by_jti, %s)
                    WHERE jti = %s
                    """,
                    (revoked_at, replaced_by_jti, jti),
                )
            finally:
                cursor.close()
            connection.commit()

    def revoke_all_for_user(self, user_id: int, revoked_at: int) -> None:
        with get_connection() as connection:
            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE refresh_tokens
                    SET revoked_at = COALESCE(revoked_at, %s)
                    WHERE user_id = %s
                    """,
                    (revoked_at, user_id),
                )
            finally:
                cursor.close()
            connection.commit()
