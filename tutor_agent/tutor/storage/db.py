"""SQLite persistence (WAL mode, every write in a transaction for crash safety)."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from tutor.domain import (
    Attempt,
    Evidence,
    Exercise,
    MasteryState,
    Message,
    Session,
    SessionStatus,
    SessionSummary,
    StudentProfile,
)

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL, updated TEXT);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY, subject TEXT, topic TEXT, status TEXT, data TEXT NOT NULL,
    created TEXT, updated TEXT);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT, kind TEXT, content TEXT, meta TEXT, created TEXT);
CREATE INDEX IF NOT EXISTS ix_messages_session ON messages(session_id, created);
CREATE TABLE IF NOT EXISTS exercises (
    id TEXT PRIMARY KEY, session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    subject TEXT, topic TEXT, concept TEXT, data TEXT NOT NULL, created TEXT);
CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY, exercise_id TEXT, session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    data TEXT NOT NULL, created TEXT);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY, subject TEXT, topic TEXT, concept TEXT, kind TEXT, session_id TEXT,
    data TEXT NOT NULL, created TEXT);
CREATE INDEX IF NOT EXISTS ix_evidence_concept ON evidence(subject, topic, concept);
CREATE TABLE IF NOT EXISTS overrides (
    subject TEXT, topic TEXT, concept TEXT, state TEXT, note TEXT, created TEXT,
    PRIMARY KEY (subject, topic, concept));
CREATE TABLE IF NOT EXISTS materials (
    id TEXT PRIMARY KEY, filename TEXT, path TEXT, sha256 TEXT UNIQUE, subject TEXT, pages INTEGER,
    status TEXT, note TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS material_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, material_id TEXT REFERENCES materials(id) ON DELETE CASCADE,
    page INTEGER, text TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(text, content='material_chunks', content_rowid='id');
CREATE TRIGGER IF NOT EXISTS chunk_ai AFTER INSERT ON material_chunks BEGIN
  INSERT INTO chunk_fts(rowid, text) VALUES (new.id, new.text); END;
CREATE TRIGGER IF NOT EXISTS chunk_ad AFTER DELETE ON material_chunks BEGIN
  INSERT INTO chunk_fts(chunk_fts, rowid, text) VALUES ('delete', old.id, old.text); END;
"""


def _iso(dt: datetime) -> str:
    return dt.isoformat()


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path) if path != ":memory:" else path
        if isinstance(self.path, Path):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        if path != ":memory:":
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = NORMAL")
        with self._lock:
            self.conn.executescript(SCHEMA)  # executescript manages its own transaction
        with self.tx() as c:
            c.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self.conn.execute("BEGIN")
            try:
                yield self.conn
            except BaseException:
                self.conn.execute("ROLLBACK")
                raise
            else:
                self.conn.execute("COMMIT")

    def query(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self.conn.execute(sql, args).fetchall()

    # ------------------------------------------------------------ profile
    def load_profile(self) -> StudentProfile:
        rows = self.query("SELECT data FROM profile WHERE id = 1")
        return StudentProfile.model_validate_json(rows[0]["data"]) if rows else StudentProfile()

    def save_profile(self, profile: StudentProfile) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO profile VALUES (1, ?, ?) ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated = excluded.updated",
                (profile.model_dump_json(), _iso(datetime.now())),
            )

    def delete_profile(self) -> None:
        with self.tx() as c:
            c.execute("DELETE FROM profile")

    # ------------------------------------------------------------ sessions
    def save_session(self, s: Session) -> None:
        s.updated = datetime.now(s.created.tzinfo)
        with self.tx() as c:
            c.execute(
                """INSERT INTO sessions VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                   subject=excluded.subject, topic=excluded.topic, status=excluded.status, data=excluded.data,
                   updated=excluded.updated""",
                (s.id, s.subject, s.topic, s.status.value, s.model_dump_json(), _iso(s.created), _iso(s.updated)),
            )

    def get_session(self, session_id: str) -> Session | None:
        rows = self.query("SELECT data FROM sessions WHERE id = ?", (session_id,))
        return Session.model_validate_json(rows[0]["data"]) if rows else None

    def list_sessions(self, limit: int = 50, status: SessionStatus | None = None) -> list[Session]:
        if status:
            rows = self.query("SELECT data FROM sessions WHERE status = ? ORDER BY updated DESC LIMIT ?", (status.value, limit))
        else:
            rows = self.query("SELECT data FROM sessions ORDER BY updated DESC LIMIT ?", (limit,))
        return [Session.model_validate_json(r["data"]) for r in rows]

    def last_session_for(self, subject: str, topic: str, exclude_id: str = "") -> Session | None:
        rows = self.query(
            "SELECT data FROM sessions WHERE subject = ? AND lower(topic) = lower(?) AND id != ? ORDER BY updated DESC LIMIT 1",
            (subject, topic, exclude_id),
        )
        return Session.model_validate_json(rows[0]["data"]) if rows else None

    def delete_session(self, session_id: str) -> None:
        with self.tx() as c:
            c.execute("DELETE FROM evidence WHERE session_id = ?", (session_id,))
            c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    # ------------------------------------------------------------ messages
    def add_message(self, m: Message) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT OR REPLACE INTO messages VALUES (?,?,?,?,?,?,?)",
                (m.id, m.session_id, m.role.value, m.kind.value, m.content, json.dumps(m.meta), _iso(m.created)),
            )
            c.execute("UPDATE sessions SET updated = ? WHERE id = ?", (_iso(m.created), m.session_id))

    def messages(self, session_id: str) -> list[Message]:
        rows = self.query("SELECT * FROM messages WHERE session_id = ? ORDER BY created, rowid", (session_id,))
        return [
            Message(id=r["id"], session_id=r["session_id"], role=r["role"], kind=r["kind"], content=r["content"],
                    meta=json.loads(r["meta"] or "{}"), created=r["created"])
            for r in rows
        ]

    # ------------------------------------------------------------ exercises / attempts
    def save_exercise(self, ex: Exercise) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT OR REPLACE INTO exercises VALUES (?,?,?,?,?,?,?)",
                (ex.id, ex.session_id or None, ex.subject, ex.topic, ex.concept, ex.model_dump_json(), _iso(ex.created)),
            )

    def get_exercise(self, ex_id: str) -> Exercise | None:
        rows = self.query("SELECT data FROM exercises WHERE id = ?", (ex_id,))
        return Exercise.model_validate_json(rows[0]["data"]) if rows else None

    def exercises_for_session(self, session_id: str) -> list[Exercise]:
        rows = self.query("SELECT data FROM exercises WHERE session_id = ? ORDER BY created", (session_id,))
        return [Exercise.model_validate_json(r["data"]) for r in rows]

    def save_attempt(self, a: Attempt) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT OR REPLACE INTO attempts VALUES (?,?,?,?,?)",
                (a.id, a.exercise_id, a.session_id, a.model_dump_json(), _iso(a.created)),
            )

    def attempts_for_session(self, session_id: str) -> list[Attempt]:
        rows = self.query("SELECT data FROM attempts WHERE session_id = ? ORDER BY created", (session_id,))
        return [Attempt.model_validate_json(r["data"]) for r in rows]

    # ------------------------------------------------------------ evidence
    def add_evidence(self, e: Evidence) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO evidence VALUES (?,?,?,?,?,?,?,?)",
                (e.id, e.subject, e.topic, e.concept, e.kind.value, e.session_id, e.model_dump_json(), _iso(e.created)),
            )

    def evidence(self, subject: str | None = None, topic: str | None = None, concept: str | None = None) -> list[Evidence]:
        sql, args = "SELECT data FROM evidence WHERE 1=1", []
        for col, val in (("subject", subject), ("topic", topic), ("concept", concept)):
            if val is not None:
                sql += f" AND lower({col}) = lower(?)"
                args.append(val)
        rows = self.query(sql + " ORDER BY created", tuple(args))
        return [Evidence.model_validate_json(r["data"]) for r in rows]

    def set_override(self, subject: str, topic: str, concept: str, state: MasteryState | None, note: str = "") -> None:
        with self.tx() as c:
            if state is None:
                c.execute("DELETE FROM overrides WHERE subject=? AND topic=? AND concept=?", (subject, topic, concept))
            else:
                c.execute("INSERT OR REPLACE INTO overrides VALUES (?,?,?,?,?,?)",
                          (subject, topic, concept, state.value, note, _iso(datetime.now())))

    def overrides(self) -> dict[tuple[str, str, str], tuple[MasteryState, str]]:
        return {
            (r["subject"], r["topic"], r["concept"]): (MasteryState(r["state"]), r["note"] or "")
            for r in self.query("SELECT * FROM overrides")
        }

    # ------------------------------------------------------------ materials
    def add_material(self, mid: str, filename: str, path: str, sha: str, subject: str, pages: int, status: str,
                     note: str, chunks: list[tuple[int, str]]) -> None:
        with self.tx() as c:
            c.execute("INSERT INTO materials VALUES (?,?,?,?,?,?,?,?,?)",
                      (mid, filename, path, sha, subject, pages, status, note, _iso(datetime.now())))
            c.executemany("INSERT INTO material_chunks (material_id, page, text) VALUES (?,?,?)",
                          [(mid, p, t) for p, t in chunks])

    def material_by_hash(self, sha: str) -> sqlite3.Row | None:
        rows = self.query("SELECT * FROM materials WHERE sha256 = ?", (sha,))
        return rows[0] if rows else None

    def list_materials(self) -> list[sqlite3.Row]:
        return self.query("SELECT * FROM materials ORDER BY created DESC")

    def delete_material(self, mid: str) -> sqlite3.Row | None:
        rows = self.query("SELECT * FROM materials WHERE id = ?", (mid,))
        with self.tx() as c:
            c.execute("DELETE FROM material_chunks WHERE material_id = ?", (mid,))
            c.execute("DELETE FROM materials WHERE id = ?", (mid,))
        return rows[0] if rows else None

    def search_chunks(self, fts_query: str, subject: str | None, limit: int = 4) -> list[sqlite3.Row]:
        sql = """SELECT mc.page, mc.text, m.filename, m.id AS material_id, bm25(chunk_fts) AS score
                 FROM chunk_fts JOIN material_chunks mc ON mc.id = chunk_fts.rowid
                 JOIN materials m ON m.id = mc.material_id
                 WHERE chunk_fts MATCH ?"""
        args: list[Any] = [fts_query]
        if subject:
            sql += " AND (m.subject = ? OR m.subject = '' OR m.subject IS NULL)"
            args.append(subject)
        sql += " ORDER BY score LIMIT ?"
        args.append(limit)
        try:
            return self.query(sql, tuple(args))
        except sqlite3.OperationalError:
            return []

    # ------------------------------------------------------------ maintenance
    def delete_all_history(self) -> None:
        with self.tx() as c:
            for t in ("attempts", "exercises", "messages", "evidence", "overrides", "sessions"):
                c.execute(f"DELETE FROM {t}")

    def backup_to(self, target: Path) -> None:
        dst = sqlite3.connect(str(target))
        try:
            with self._lock:
                self.conn.backup(dst)
        finally:
            dst.close()

    def save_summary(self, session: Session, summary: SessionSummary) -> None:
        session.summary = summary
        session.status = SessionStatus.COMPLETED
        self.save_session(session)
