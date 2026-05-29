from typing import Any, Optional, cast

try:
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    dict_row = None

from app.core.database import get_connection, init_database, use_postgres
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
            if use_postgres():
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
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                    """,
                    (username, password_hash),
                )
                user_id = int(cast(Any, cursor).lastrowid or 0)
                row = connection.execute(
                    """
                    SELECT id, username, password_hash
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,),
                ).fetchone()
            connection.commit()

        if row is None:
            raise RuntimeError("Failed to create user")
        return self._row_to_user(row)

    def get_by_username(self, username: str) -> Optional[User]:
        with get_connection() as connection:
            if use_postgres():
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
            else:
                row = connection.execute(
                    """
                    SELECT id, username, password_hash
                    FROM users
                    WHERE username = ?
                    """,
                    (username,),
                ).fetchone()

        if row is None:
            return None
        return self._row_to_user(row)

    def get_by_id(self, user_id: int) -> Optional[User]:
        with get_connection() as connection:
            if use_postgres():
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
            else:
                row = connection.execute(
                    """
                    SELECT id, username, password_hash
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,),
                ).fetchone()

        if row is None:
            return None
        return self._row_to_user(row)
