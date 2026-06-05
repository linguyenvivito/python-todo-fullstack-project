
from typing import List, Optional

from app.core.database import get_connection, init_database
from app.core.models import Role

class RoleRepository:
    def __init__(self):
        init_database()

    def list_all(self) -> List[Role]:
        with get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT id, name FROM roles ORDER BY id")
                roles = cursor.fetchall()
                return [Role(id=row[0], name=row[1]) for row in roles]
            finally:
                cursor.close()

    def get_by_name(self, name: str) -> Optional[Role]:
        with get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT id, name FROM roles WHERE name = %s", (name,))
                row = cursor.fetchone()
                if row is None:
                    return None
                return Role(id=row[0], name=row[1])
            finally:
                cursor.close()

    def create(self, name: str) -> Role:
        with get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO roles (name)
                    VALUES (%s)
                    RETURNING id, name
                    """,
                    (name,),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
            connection.commit()

        if row is None:
            raise RuntimeError("Failed to create role")
        return Role(id=row[0], name=row[1])

    def get_by_id(self, role_id: int) -> Optional[Role]:
        with get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT id, name FROM roles WHERE id = %s", (role_id,))
                row = cursor.fetchone()
                if row is None:
                    return None
                return Role(id=row[0], name=row[1])
            finally:
                cursor.close()

    def update(self, role_id: int, name: str) -> Optional[Role]:
        with get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE roles
                    SET name = %s
                    WHERE id = %s
                    RETURNING id, name
                    """,
                    (name, role_id),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
            connection.commit()

        if row is None:
            return None
        return Role(id=row[0], name=row[1])

    def delete(self, role_id: int) -> bool:
        with get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("DELETE FROM roles WHERE id = %s", (role_id,))
                deleted = cursor.rowcount > 0
            finally:
                cursor.close()
            connection.commit()

        return deleted