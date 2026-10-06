"""SQLite persistence for chat users and messages."""

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import IntegrityError

from auth import hash_password, verify_password


# Set CHAT_DB_PATH to store the database somewhere else, such as in Docker.
DATABASE_PATH = Path(
    os.environ.get("CHAT_DB_PATH", Path(__file__).with_name("chat.db"))
).expanduser().resolve()
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = URL.create("sqlite", database=str(DATABASE_PATH))
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
)


def init_db() -> None:
    """Create the database tables if they do not already exist."""
    users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """
    messages_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """

    with engine.begin() as connection:
        connection.exec_driver_sql(users_sql)
        connection.exec_driver_sql(messages_sql)


def create_user(username: str, password: str) -> bool:
    """Create a user. Return False if the username is already taken."""
    username = username.strip()
    if not username or not password:
        raise ValueError("Username and password cannot be empty.")

    salt_hex, password_hash_hex = hash_password(password)
    insert_sql = """
        INSERT INTO users (username, password_salt, password_hash)
        VALUES (:username, :salt, :password_hash)
    """

    try:
        with engine.begin() as connection:
            connection.execute(
                text(insert_sql),
                {
                    "username": username,
                    "salt": salt_hex,
                    "password_hash": password_hash_hex,
                },
            )
        return True
    except IntegrityError:
        return False


def _get_user_credentials(username: str) -> tuple[str, str] | None:
    """Return a user's stored salt and password hash, or None if absent."""
    query = text("""
        SELECT password_salt, password_hash
        FROM users
        WHERE username = :username
    """)

    with engine.connect() as connection:
        row = connection.execute(query, {"username": username}).first()

    if row is None:
        return None

    return row[0], row[1]


def authenticate_user(username: str, password: str) -> bool:
    """Return whether the supplied username and password are valid."""
    credentials = _get_user_credentials(username.strip())
    if credentials is None:
        return False

    salt_hex, stored_hash_hex = credentials
    return verify_password(password, salt_hex, stored_hash_hex)


def save_message(username: str, content: str) -> None:
    """Save a message with a UTC timestamp."""
    insert_sql = text("""
        INSERT INTO messages (username, content, created_at)
        VALUES (:username, :content, :created_at)
    """)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with engine.begin() as connection:
        connection.execute(
            insert_sql,
            {
                "username": username,
                "content": content,
                "created_at": created_at,
            },
        )


def get_recent_messages(limit: int = 20) -> list[tuple[str, str, str]]:
    """Return up to `limit` recent messages in chronological order."""
    if limit <= 0:
        return []

    query = text("""
        SELECT username, content, created_at
        FROM messages
        ORDER BY message_id DESC
        LIMIT :limit
    """)

    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).all()

    return [(row[0], row[1], row[2]) for row in reversed(rows)]