import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
SQL_PATH = BASE_DIR / "instance" / "hospital_demo.sql"
DATABASE = BASE_DIR / "instance" / "hospital_demo.db"


def init_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    if DATABASE.exists():
        DATABASE.unlink()

    connection = sqlite3.connect(DATABASE)
    sql_script = SQL_PATH.read_text(encoding="utf-8")
    connection.executescript(sql_script)

    # Insert admin with hashed password
    connection.execute(
        "INSERT INTO users (username, password, role, linked_id) VALUES (?, ?, 'admin', NULL)",
        ("admin1", generate_password_hash("admin123")),
    )
    connection.commit()
    connection.close()
    print(f"Database initialized at {DATABASE}")


if __name__ == "__main__":
    init_db()
