"""SQLite persistence for settings, lesson progress and every assessment attempt.

The application is single-user and local, so a small SQLite file is enough.
All writes go through this module; every function opens a short-lived
connection so the store is safe to use from Streamlit reruns.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

from analytics_lab.config import DEFAULT_SETTINGS, get_paths

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lesson_progress (
    lesson_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'in_progress',
    check_score REAL,
    started_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE TABLE IF NOT EXISTS quiz_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,                -- practice | exam | lesson_check | final
    started_at TEXT NOT NULL,
    finished_at TEXT,
    n_questions INTEGER NOT NULL,
    n_correct INTEGER,
    score REAL,
    time_limit_min REAL,
    timed_out INTEGER DEFAULT 0,
    config TEXT
);
CREATE TABLE IF NOT EXISTS question_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER,
    question_id TEXT NOT NULL,
    module TEXT, topic TEXT, competency TEXT, difficulty TEXT,
    chosen TEXT,
    correct INTEGER NOT NULL,
    answered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exercise_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id TEXT NOT NULL,
    language TEXT, module TEXT,
    submitted_at TEXT NOT NULL,
    passed INTEGER NOT NULL,
    score REAL NOT NULL,
    hints_used INTEGER DEFAULT 0,
    solution_viewed INTEGER DEFAULT 0,
    code TEXT,
    feedback TEXT
);
CREATE TABLE IF NOT EXISTS case_submissions (
    submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    answer TEXT,
    objective_score REAL,
    self_scores TEXT,
    self_score REAL,
    total_score REAL
);
CREATE TABLE IF NOT EXISTS capstone_milestones (
    capstone_id TEXT NOT NULL,
    milestone_id TEXT NOT NULL,
    status TEXT NOT NULL,
    score REAL,
    evidence TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (capstone_id, milestone_id)
);
CREATE TABLE IF NOT EXISTS tool_tasks (
    task_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    score REAL,
    detail TEXT,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activity (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    ref TEXT,
    detail TEXT
);
CREATE INDEX IF NOT EXISTS ix_resp_q ON question_responses(question_id);
CREATE INDEX IF NOT EXISTS ix_ex_id ON exercise_attempts(exercise_id);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class ProgressStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else get_paths().progress_db
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    # ------------------------------------------------------------------ infra
    @contextmanager
    def conn(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init(self) -> None:
        try:
            with self.conn() as c:
                c.executescript(SCHEMA)
                c.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
        except sqlite3.DatabaseError as exc:
            # A corrupted file should not brick the app: keep a backup and start fresh.
            backup = self.path.with_suffix(f".corrupt-{datetime.now():%Y%m%d%H%M%S}.db")
            self.path.replace(backup)
            with self.conn() as c:
                c.executescript(SCHEMA)
            self._log_internal("recovered_corrupt_db", str(backup), str(exc))

    def _log_internal(self, kind: str, ref: str, detail: str) -> None:
        with self.conn() as c:
            c.execute("INSERT INTO activity(ts, kind, ref, detail) VALUES (?,?,?,?)", (_now(), kind, ref, detail))

    def df(self, sql: str, params: tuple = ()) -> pd.DataFrame:
        with self.conn() as c:
            return pd.read_sql_query(sql, c, params=params)

    # --------------------------------------------------------------- settings
    def get_setting(self, key: str) -> str:
        with self.conn() as c:
            row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else DEFAULT_SETTINGS.get(key, "")

    def get_settings(self) -> dict[str, str]:
        out = dict(DEFAULT_SETTINGS)
        with self.conn() as c:
            out.update({r["key"]: r["value"] for r in c.execute("SELECT key, value FROM settings")})
        return out

    def set_setting(self, key: str, value: Any) -> None:
        with self.conn() as c:
            c.execute("INSERT INTO settings VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

    # ---------------------------------------------------------------- activity
    def log(self, kind: str, ref: str = "", detail: str = "") -> None:
        self._log_internal(kind, ref, detail)

    def activity_days(self) -> list[date]:
        with self.conn() as c:
            rows = c.execute("SELECT DISTINCT substr(ts, 1, 10) d FROM activity WHERE kind NOT LIKE 'recovered%' ORDER BY d").fetchall()
        return [date.fromisoformat(r["d"]) for r in rows]

    def streak(self, today: date | None = None) -> int:
        """Consecutive days with activity, ending today or yesterday."""
        days = set(self.activity_days())
        today = today or date.today()
        cur = today if today in days else today - timedelta(days=1)
        n = 0
        while cur in days:
            n += 1
            cur -= timedelta(days=1)
        return n

    def recent_activity(self, limit: int = 15) -> pd.DataFrame:
        return self.df("SELECT ts, kind, ref, detail FROM activity ORDER BY activity_id DESC LIMIT ?", (limit,))

    # ----------------------------------------------------------------- lessons
    def start_lesson(self, lesson_id: str) -> None:
        with self.conn() as c:
            c.execute("INSERT OR IGNORE INTO lesson_progress(lesson_id, status, started_at) VALUES (?, 'in_progress', ?)", (lesson_id, _now()))

    def complete_lesson(self, lesson_id: str, check_score: float | None = None) -> None:
        self.start_lesson(lesson_id)
        with self.conn() as c:
            c.execute(
                "UPDATE lesson_progress SET status='completed', completed_at=COALESCE(completed_at, ?), check_score=COALESCE(?, check_score) WHERE lesson_id=?",
                (_now(), check_score, lesson_id),
            )
        self.log("lesson_completed", lesson_id)

    def lesson_status(self) -> dict[str, dict]:
        with self.conn() as c:
            return {r["lesson_id"]: dict(r) for r in c.execute("SELECT * FROM lesson_progress")}

    def completed_lessons(self) -> set[str]:
        return {k for k, v in self.lesson_status().items() if v["status"] == "completed"}

    # ------------------------------------------------------------------ quizzes
    def start_quiz(self, kind: str, n_questions: int, time_limit_min: float | None = None, config: dict | None = None) -> int:
        with self.conn() as c:
            cur = c.execute(
                "INSERT INTO quiz_attempts(kind, started_at, n_questions, time_limit_min, config) VALUES (?,?,?,?,?)",
                (kind, _now(), n_questions, time_limit_min, json.dumps(config or {})),
            )
            return int(cur.lastrowid)

    def record_response(self, attempt_id: int | None, question, chosen: list[str], correct: bool) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO question_responses(attempt_id, question_id, module, topic, competency, difficulty, chosen, correct, answered_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (attempt_id, question.id, question.module, question.topic, question.competency, question.difficulty, json.dumps(chosen), int(correct), _now()),
            )

    def finish_quiz(self, attempt_id: int, n_correct: int, timed_out: bool = False) -> None:
        with self.conn() as c:
            row = c.execute("SELECT n_questions FROM quiz_attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
            n = row["n_questions"] if row else 0
            c.execute(
                "UPDATE quiz_attempts SET finished_at=?, n_correct=?, score=?, timed_out=? WHERE attempt_id=?",
                (_now(), n_correct, round(100 * n_correct / n, 1) if n else 0, int(timed_out), attempt_id),
            )
        self.log("quiz_finished", str(attempt_id), f"{n_correct}/{n}")

    def responses(self) -> pd.DataFrame:
        return self.df("SELECT * FROM question_responses ORDER BY response_id")

    def quiz_history(self) -> pd.DataFrame:
        return self.df("SELECT * FROM quiz_attempts WHERE finished_at IS NOT NULL ORDER BY attempt_id")

    def attempt_responses(self, attempt_id: int) -> pd.DataFrame:
        return self.df("SELECT * FROM question_responses WHERE attempt_id=? ORDER BY response_id", (attempt_id,))

    # ---------------------------------------------------------------- exercises
    def record_exercise(self, exercise, passed: bool, score: float, code: str, feedback: dict, hints_used: int = 0, solution_viewed: bool = False) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO exercise_attempts(exercise_id, language, module, submitted_at, passed, score, hints_used, solution_viewed, code, feedback) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (exercise.id, exercise.language, exercise.module, _now(), int(passed), float(score), hints_used, int(solution_viewed), code, json.dumps(feedback, default=str)),
            )
        self.log("exercise_submitted", exercise.id, f"score={score:.0f}")

    def exercise_attempts(self, exercise_id: str | None = None) -> pd.DataFrame:
        if exercise_id:
            return self.df("SELECT * FROM exercise_attempts WHERE exercise_id=? ORDER BY attempt_id", (exercise_id,))
        return self.df("SELECT * FROM exercise_attempts ORDER BY attempt_id")

    def exercise_summary(self) -> pd.DataFrame:
        """Best score per exercise. Passing after viewing the solution counts as assisted."""
        return self.df(
            """
            SELECT exercise_id, module, language, COUNT(*) attempts, MAX(score) best_score, MAX(passed) passed,
                   MIN(CASE WHEN passed=1 THEN attempt_id END) first_pass_attempt,
                   MAX(CASE WHEN passed=1 AND solution_viewed=0 THEN 1 ELSE 0 END) passed_unassisted,
                   MAX(submitted_at) last_attempt
            FROM exercise_attempts GROUP BY exercise_id, module, language
            """
        )

    # -------------------------------------------------------------------- cases
    def record_case(self, case_id: str, answer: str, objective_score: float | None, self_scores: dict, self_score: float | None, total: float) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO case_submissions(case_id, submitted_at, answer, objective_score, self_scores, self_score, total_score) VALUES (?,?,?,?,?,?,?)",
                (case_id, _now(), answer, objective_score, json.dumps(self_scores), self_score, total),
            )
        self.log("case_submitted", case_id, f"score={total:.0f}")

    def case_submissions(self) -> pd.DataFrame:
        return self.df("SELECT * FROM case_submissions ORDER BY submission_id")

    # ---------------------------------------------------------------- capstones
    def set_milestone(self, capstone_id: str, milestone_id: str, status: str, score: float | None = None, evidence: str = "") -> None:
        with self.conn() as c:
            c.execute(
                """INSERT INTO capstone_milestones VALUES (?,?,?,?,?,?)
                   ON CONFLICT(capstone_id, milestone_id) DO UPDATE SET status=excluded.status,
                   score=COALESCE(excluded.score, capstone_milestones.score), evidence=excluded.evidence, updated_at=excluded.updated_at""",
                (capstone_id, milestone_id, status, score, evidence, _now()),
            )
        self.log("milestone_updated", f"{capstone_id}/{milestone_id}", status)

    def milestones(self, capstone_id: str | None = None) -> pd.DataFrame:
        if capstone_id:
            return self.df("SELECT * FROM capstone_milestones WHERE capstone_id=?", (capstone_id,))
        return self.df("SELECT * FROM capstone_milestones")

    # --------------------------------------------------------------- tool tasks
    def set_tool_task(self, task_id: str, status: str, score: float | None = None, detail: str = "") -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO tool_tasks VALUES (?,?,?,?,?) ON CONFLICT(task_id) DO UPDATE SET status=excluded.status, score=excluded.score, detail=excluded.detail, updated_at=excluded.updated_at",
                (task_id, status, score, detail, _now()),
            )
        self.log("tool_task", task_id, status)

    def tool_tasks(self) -> pd.DataFrame:
        return self.df("SELECT * FROM tool_tasks")

    # ------------------------------------------------------------ export/reset
    def export_all(self) -> dict[str, list[dict]]:
        tables = ["settings", "lesson_progress", "quiz_attempts", "question_responses", "exercise_attempts", "case_submissions", "capstone_milestones", "tool_tasks", "activity"]
        return {t: self.df(f"SELECT * FROM {t}").to_dict(orient="records") for t in tables}

    def reset(self, keep_settings: bool = True) -> None:
        tables = ["lesson_progress", "quiz_attempts", "question_responses", "exercise_attempts", "case_submissions", "capstone_milestones", "tool_tasks", "activity"]
        if not keep_settings:
            tables.append("settings")
        with self.conn() as c:
            for t in tables:
                c.execute(f"DELETE FROM {t}")
