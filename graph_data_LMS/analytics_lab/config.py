"""Central configuration: filesystem locations and default settings.

All paths can be relocated with the ``ANALYTICS_LAB_HOME`` environment variable,
which is mainly useful for tests (each test run gets its own throwaway home).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent


@dataclass(frozen=True)
class Paths:
    home: Path

    @property
    def data_dir(self) -> Path:
        return self.home / "data"

    @property
    def generated_dir(self) -> Path:
        return self.data_dir / "generated"

    @property
    def csv_dir(self) -> Path:
        return self.generated_dir / "csv"

    @property
    def warehouse_db(self) -> Path:
        """DuckDB file holding every generated dataset (read-only for learners)."""
        return self.generated_dir / "lab.duckdb"

    @property
    def uploads_db(self) -> Path:
        """DuckDB file holding tables imported by the user."""
        return self.data_dir / "uploads.duckdb"

    @property
    def progress_db(self) -> Path:
        """SQLite file holding progress, attempts and settings."""
        return self.data_dir / "progress.db"

    @property
    def manifest(self) -> Path:
        return self.generated_dir / "manifest.json"

    def ensure(self) -> None:
        self.csv_dir.mkdir(parents=True, exist_ok=True)


def get_paths() -> Paths:
    home = os.environ.get("ANALYTICS_LAB_HOME")
    return Paths(Path(home).resolve() if home else PROJECT_ROOT)


# Default values for user-editable settings (persisted in SQLite).
DEFAULT_SETTINGS: dict[str, str] = {
    "mastery_threshold": "80",          # percent
    "execution_timeout": "20",          # seconds per code run
    "execution_backend": "local",       # "local" subprocess or "docker"
    "docker_image": "analytics-lab-runner:latest",
    "quiz_feedback": "immediate",       # "immediate" or "end"
    "r_executable": "",                 # optional explicit path to Rscript
    "learner_name": "",
    "language": "en",                   # "en" English or "cs" Czech (interface and learning content)
    "theme": "light",                   # "light" or "dark"
}

# Bump when the dataset generator changes so stale data is regenerated.
DATASET_VERSION = "1.0"

MAX_OUTPUT_CHARS = 20_000
MAX_RESULT_ROWS = 5_000
