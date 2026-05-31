import argparse
import os
from typing import List, Sequence, Tuple

from app.core.database import get_connection, init_database
from app.core.security import hash_password

DEFAULT_TASKS: List[Tuple[str, str]] = [
    ("Plan sprint backlog", "Break down user stories for this week"),
    ("Implement JWT refresh", "Add refresh token endpoint and rotation"),
    ("Write API integration tests", "Cover auth and task ownership scenarios"),
    ("Refactor task board UI", "Improve mobile layout and empty states"),
    ("Prepare deployment checklist", "Verify env vars, health checks, and logs"),
]


def ensure_demo_user(username: str, password: str) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            row = cursor.fetchone()
            if row:
                connection.commit()
                return int(row[0])

            cursor.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (%s, %s)
                RETURNING id
                """,
                (username, hash_password(password)),
            )
            created_row = cursor.fetchone()
            if created_row is None:
                raise RuntimeError("Failed to create demo user")
            user_id = int(created_row[0])
        finally:
            cursor.close()

        connection.commit()
        return user_id


def seed_tasks_for_user(user_id: int, tasks: Sequence[Tuple[str, str]], force: bool) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        try:
            if force:
                cursor.execute("DELETE FROM tasks WHERE user_id = %s", (user_id,))

            cursor.execute(
                "SELECT COUNT(1) FROM tasks WHERE user_id = %s",
                (user_id,),
            )
            count_row = cursor.fetchone()
            existing_count = int(count_row[0]) if count_row else 0

            if existing_count > 0 and not force:
                connection.commit()
                return 0

            for title, description in tasks:
                cursor.execute(
                    """
                    INSERT INTO tasks (title, description, status, user_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (title, description, "todo", user_id),
                )
        finally:
            cursor.close()

        connection.commit()
        return len(tasks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo user and todo tasks")
    parser.add_argument("--force", action="store_true", help="Replace existing tasks for the seeded user")
    args = parser.parse_args()

    init_database()

    username = os.getenv("SEED_DEMO_USERNAME", "demo")
    password = os.getenv("SEED_DEMO_PASSWORD", "demo123")

    user_id = ensure_demo_user(username, password)
    created = seed_tasks_for_user(user_id, DEFAULT_TASKS, args.force)

    if created == 0:
        print(f"No tasks seeded. User '{username}' already has tasks. Use --force to reseed.")
    else:
        print(f"Seeded {created} todo tasks for user '{username}'.")

    print(f"Login credentials -> username: {username}, password: {password}")


if __name__ == "__main__":
    main()
