import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "instance" / "demo.db"


def init_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE)

    connection.execute("DROP TABLE IF EXISTS users")
    connection.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    sample_users = [
        ("student", "password123", 0),
        ("admin", "admin", 1),
    ]

    for username, password, is_admin in sample_users:
        connection.execute(
            """
            INSERT INTO users (username, password, is_admin)
            VALUES (?, ?, ?)
            """,
            (username, password, is_admin),
        )

    connection.commit()
    connection.close()
    print(f"Database initialized at {DATABASE}")


if __name__ == "__main__":
    init_db()
