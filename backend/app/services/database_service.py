from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.config import SQLITE_PATH

MAX_HISTORY_MESSAGES = 20

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    last_message_preview TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        conn.commit()


def ensure_conversation(session_id: str, last_message_preview: str) -> None:
    with _connect() as conn:
        existing = conn.execute(
            "SELECT 1 FROM conversations WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO conversations (session_id, created_at, last_message_preview) VALUES (?, ?, ?)",
                (session_id, _now(), last_message_preview),
            )
        else:
            conn.execute(
                "UPDATE conversations SET last_message_preview = ? WHERE session_id = ?",
                (last_message_preview, session_id),
            )
        conn.commit()


def add_chat_message(session_id: str, role: str, content: str) -> None:
    ensure_conversation(session_id, content[:70])
    with _connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, _now()),
        )
        conn.commit()


def get_chat_history(session_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, MAX_HISTORY_MESSAGES),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def list_conversations() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT session_id, created_at, last_message_preview
            FROM conversations
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_conversation_messages(session_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]
