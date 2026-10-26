"""Backup / restore of learning progress and Markdown exports."""

from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from tutor import __version__
from tutor.app_paths import AppPaths, unique_path
from tutor.domain import MessageKind, Role, Session
from tutor.storage.db import Database

MANIFEST = "manifest.json"


def create_backup(db: Database, paths: AppPaths, target: Path | None = None, include_materials: bool = True) -> Path:
    """Write a consistent zip backup; never overwrites an existing file."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = unique_path(target or paths.backups / f"tutor-backup-{stamp}.zip")
    with tempfile.TemporaryDirectory() as tmp:
        snap = Path(tmp) / "tutor.sqlite3"
        db.backup_to(snap)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(snap, "tutor.sqlite3")
            if include_materials:
                for f in paths.materials.glob("*"):
                    if f.is_file():
                        zf.write(f, f"materials/{f.name}")
            zf.writestr(MANIFEST, json.dumps({"app_version": __version__, "created": stamp, "kind": "PersonalAITutor backup"}))
    return target


def validate_backup(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if MANIFEST not in names or "tutor.sqlite3" not in names:
            raise ValueError("This file is not a Personal AI Tutor backup.")
        for n in names:
            if n.startswith(("/", "\\")) or ".." in Path(n).parts:
                raise ValueError("Backup contains unsafe paths.")


def restore_backup(db_path: Path, paths: AppPaths, backup: Path) -> Path:
    """Restore ``backup``. The current database is first backed up (returned path).

    The caller must close and reopen its :class:`Database` afterwards.
    """
    validate_backup(backup)
    safety = unique_path(paths.backups / f"before-restore-{datetime.now():%Y%m%d-%H%M%S}.sqlite3")
    if db_path.exists():
        src = sqlite3.connect(str(db_path))
        dst = sqlite3.connect(str(safety))
        try:
            src.backup(dst)
        finally:
            src.close()
            dst.close()
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(backup) as zf:
        zf.extractall(tmp)
        restored = Path(tmp) / "tutor.sqlite3"
        check = sqlite3.connect(str(restored))
        try:
            if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("The backup database is damaged.")
        finally:
            check.close()
        for suffix in ("-wal", "-shm"):
            Path(str(db_path) + suffix).unlink(missing_ok=True)
        shutil.copy2(restored, db_path)
        mat = Path(tmp) / "materials"
        if mat.exists():
            for f in mat.iterdir():
                dest = paths.materials / f.name
                if not dest.exists():  # preserve existing user files
                    shutil.copy2(f, dest)
    return safety


def session_to_markdown(db: Database, session: Session) -> str:
    lines = [f"# {session.subject}: {session.topic}", ""]
    lines.append(f"*Date:* {session.created:%Y-%m-%d}  ·  *Level:* {session.level}  ·  *Style:* {session.style.label}")
    if session.goal:
        lines.append(f"*Goal:* {session.goal}")
    lines.append("")
    if session.summary:
        s = session.summary
        lines += ["## Summary", ""]
        for title, items in (("Key concepts", s.key_concepts), ("Strengths", s.strengths),
                             ("Still to work on", s.misconceptions), ("Next steps", s.next_steps)):
            if items:
                lines.append(f"**{title}**")
                lines += [f"- {i}" for i in items]
                lines.append("")
        if s.practice_task:
            lines += ["**Practice task**", "", s.practice_task, ""]
    lines += ["## Session notes", ""]
    for m in db.messages(session.id):
        if m.kind == MessageKind.NOTICE:
            continue
        who = "**You:**" if m.role == Role.USER else "**Tutor:**"
        lines += [f"{who} {m.content}", ""]
    lines.append("---\n*Exported from Personal AI Tutor. AI-generated explanations may contain errors - verify important results.*")
    return "\n".join(lines)


def export_session(db: Database, session: Session, folder: Path) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in f"{session.subject} - {session.topic}")[:80]
    path = unique_path(folder / f"{safe} {session.created:%Y-%m-%d}.md")
    path.write_text(session_to_markdown(db, session), encoding="utf-8")
    return path


def export_progress(db: Database, statuses: list, folder: Path) -> Path:
    path = unique_path(folder / f"learning-progress {datetime.now():%Y-%m-%d}.md")
    lines = ["# Learning progress", "", "| Subject | Topic | Concept | State | Evidence | Certainty |", "|---|---|---|---|---|---|"]
    for s in statuses:
        lines.append(f"| {s.subject} | {s.topic} | {s.concept} | {s.state.label} | {s.evidence_count} | {s.certainty} |")
    lines += ["", "*States are estimates based on recorded evidence, not exact measurements.*"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
