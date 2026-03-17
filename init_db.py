import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "instance" / "demo.db"


def init_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    sample_users = [
        ("student", generate_password_hash("password123"), 0),
        ("admin", generate_password_hash("admin123"), 1),
    ]

    for username, password_hash, is_admin in sample_users:
        connection.execute(
            """
            INSERT INTO users (username, password_hash, is_admin)
            VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = excluded.password_hash,
                is_admin = excluded.is_admin
            """,
            (username, password_hash, is_admin),
        )

    connection.commit()
    connection.close()
    print(f"Database initialized at {DATABASE}")


if __name__ == "__main__":
    init_db()

