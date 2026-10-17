"""Lightweight SQLite session & conversation history store.

Each session belongs to a role and stores an ordered list of chat messages.
Sessions survive server restarts (persisted to ``data/sessions.db``).
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models import ChatMessage, SessionInfo, SourceRecord


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid() -> str:
    return uuid.uuid4().hex[:12]


class SessionStore:
    def __init__(self, db_path: Path | str = "data/sessions.db"):
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _create_tables(self) -> None:
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id  TEXT PRIMARY KEY,
                role        TEXT NOT NULL,
                title       TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id          TEXT PRIMARY KEY,
                session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                role_sender TEXT NOT NULL,
                content     TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                feature_tag TEXT,
                sources     TEXT DEFAULT '[]',
                safety_boundary TEXT,
                agent_steps TEXT DEFAULT '[]',
                image_path  TEXT,
                reasoning_content TEXT,
                followup_questions TEXT DEFAULT '[]'
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
        """)
        # Automatic schema migration for existing databases
        for col, col_type in [
            ("reasoning_content", "TEXT"),
            ("followup_questions", "TEXT DEFAULT '[]'"),
        ]:
            try:
                cur.execute(f"ALTER TABLE messages ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
        self._conn.commit()

    # ------------------------------------------------------------------
    # Session CRUD
    # ------------------------------------------------------------------
    def create_session(self, role: str, title: str | None = None) -> SessionInfo:
        sid = _uid()
        now = _now()
        title = title or f"New {role.replace('_', ' ').title()} Chat"
        self._conn.execute(
            "INSERT INTO sessions (session_id, role, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (sid, role, title, now, now),
        )
        self._conn.commit()
        return SessionInfo(session_id=sid, role=role, title=title, created_at=now, updated_at=now)

    def list_sessions(self) -> list[SessionInfo]:
        rows = self._conn.execute(
            "SELECT s.*, (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.session_id) AS cnt "
            "FROM sessions s ORDER BY s.updated_at DESC"
        ).fetchall()
        return [
            SessionInfo(
                session_id=r["session_id"],
                role=r["role"],
                title=r["title"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                message_count=r["cnt"],
            )
            for r in rows
        ]

    def get_session(self, session_id: str) -> SessionInfo | None:
        r = self._conn.execute(
            "SELECT s.*, (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.session_id) AS cnt "
            "FROM sessions s WHERE s.session_id = ?",
            (session_id,),
        ).fetchone()
        if not r:
            return None
        return SessionInfo(
            session_id=r["session_id"],
            role=r["role"],
            title=r["title"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            message_count=r["cnt"],
        )

    def rename_session(self, session_id: str, title: str) -> bool:
        cur = self._conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ?",
            (title, _now(), session_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        self._conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cur = self._conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        self._conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Message CRUD
    # ------------------------------------------------------------------
    def add_message(
        self,
        session_id: str,
        role_sender: str,
        content: str,
        *,
        feature_tag: str | None = None,
        sources: list[SourceRecord] | None = None,
        safety_boundary: str | None = None,
        agent_steps: list[str] | None = None,
        image_path: str | None = None,
        reasoning_content: str | None = None,
        followup_questions: list[str] | None = None,
    ) -> ChatMessage:
        mid = _uid()
        now = _now()
        src_json = json.dumps([s.model_dump() for s in sources] if sources else [])
        steps_json = json.dumps(agent_steps or [])
        followup_json = json.dumps(followup_questions or [])
        self._conn.execute(
            "INSERT INTO messages (id, session_id, role_sender, content, timestamp, feature_tag, sources, safety_boundary, agent_steps, image_path, reasoning_content, followup_questions) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mid, session_id, role_sender, content, now, feature_tag, src_json, safety_boundary, steps_json, image_path, reasoning_content, followup_json),
        )
        self._conn.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id))
        self._conn.commit()
        return ChatMessage(
            id=mid,
            session_id=session_id,
            role_sender=role_sender,
            content=content,
            timestamp=now,
            feature_tag=feature_tag,
            sources=sources or [],
            safety_boundary=safety_boundary,
            agent_steps=agent_steps or [],
            image_path=image_path,
            reasoning_content=reasoning_content,
            followup_questions=followup_questions or [],
        )

    def get_messages(self, session_id: str) -> list[ChatMessage]:
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,),
        ).fetchall()
        return [self._row_to_message(r) for r in rows]

    def _row_to_message(self, r: sqlite3.Row) -> ChatMessage:
        keys = r.keys()
        sources_raw = json.loads(r["sources"]) if "sources" in keys and r["sources"] else []
        sources = [SourceRecord(**s) for s in sources_raw]
        agent_steps = json.loads(r["agent_steps"]) if "agent_steps" in keys and r["agent_steps"] else []
        followup_questions = json.loads(r["followup_questions"]) if "followup_questions" in keys and r["followup_questions"] else []
        reasoning_content = r["reasoning_content"] if "reasoning_content" in keys else None
        return ChatMessage(
            id=r["id"],
            session_id=r["session_id"],
            role_sender=r["role_sender"],
            content=r["content"],
            timestamp=r["timestamp"],
            feature_tag=r["feature_tag"] if "feature_tag" in keys else None,
            sources=sources,
            safety_boundary=r["safety_boundary"] if "safety_boundary" in keys else None,
            agent_steps=agent_steps,
            image_path=r["image_path"] if "image_path" in keys else None,
            reasoning_content=reasoning_content,
            followup_questions=followup_questions,
        )

    # ------------------------------------------------------------------
    # Utility: recent messages for LLM context window
    # ------------------------------------------------------------------
    def recent_messages_for_context(self, session_id: str, limit: int = 20) -> list[dict[str, str]]:
        """Return the last *limit* messages formatted for LLM ``messages`` list."""
        rows = self._conn.execute(
            "SELECT role_sender, content FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        rows = list(reversed(rows))
        return [{"role": r["role_sender"], "content": r["content"]} for r in rows]
