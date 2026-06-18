from typing import Any, List, cast

try:
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    dict_row = None

from app.core.database import get_connection, init_database
from app.core.models import User

class UserRepository:
    def __init__(self):
        init_database()

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
        )
    
    def list_all(self) -> List[User]:
        with get_connection() as connection:
            if dict_row is None:
                raise RuntimeError(
                    "PostgreSQL mode requires psycopg to be installed."
                )

            pg_connection = cast(Any, connection)
            cursor = pg_connection.cursor(row_factory=dict_row)
            try:
                cursor.execute(
                    """
                    SELECT id, username, password_hash
                    FROM users
                    ORDER BY id
                    """
                )
                rows = cursor.fetchall()
            finally:
                cursor.close()

        return [self._row_to_user(row) for row in rows]