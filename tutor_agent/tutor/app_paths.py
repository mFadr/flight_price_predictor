"""Filesystem locations for application data.

All data lives under ``%LOCALAPPDATA%\\PersonalAITutor`` by default. The location
can be overridden with the ``TUTOR_DATA_DIR`` environment variable (used by the
test-suite and by users who want portable installs).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from tutor import APP_NAME

SUBDIRS = ("profiles", "sessions", "learning_history", "materials", "exports", "cache", "logs", "backups")


def default_data_dir() -> Path:
    override = os.environ.get("TUTOR_DATA_DIR")
    if override:
        return Path(override).expanduser()
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / APP_NAME
    # Non-Windows fallback (development / CI)
    return Path.home() / ".local" / "share" / APP_NAME


@dataclass(frozen=True)
class AppPaths:
    root: Path

    @classmethod
    def create(cls, root: Path | None = None) -> "AppPaths":
        paths = cls(Path(root) if root else default_data_dir())
        paths.ensure()
        return paths

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for name in SUBDIRS:
            (self.root / name).mkdir(exist_ok=True)

    @property
    def config_file(self) -> Path:
        return self.root / "config.toml"

    @property
    def database(self) -> Path:
        return self.root / "learning_history" / "tutor.sqlite3"

    @property
    def materials(self) -> Path:
        return self.root / "materials"

    @property
    def exports(self) -> Path:
        return self.root / "exports"

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def backups(self) -> Path:
        return self.root / "backups"

    @property
    def sandbox(self) -> Path:
        p = self.cache / "sandbox"
        p.mkdir(exist_ok=True)
        return p

    @property
    def viz(self) -> Path:
        p = self.cache / "viz"
        p.mkdir(exist_ok=True)
        return p


def unique_path(path: Path) -> Path:
    """Return ``path`` or a numbered variant that does not exist yet (never overwrite)."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for i in range(2, 10_000):
        candidate = path.with_name(f"{stem} ({i}){suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Could not find a free filename for {path}")


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Write via a temporary file + replace so an interrupted write never corrupts ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding=encoding)
    os.replace(tmp, path)
