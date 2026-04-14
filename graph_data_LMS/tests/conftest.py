"""Test configuration: every test session uses its own throwaway data directory."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_HOME = Path(tempfile.mkdtemp(prefix="analytics_lab_tests_"))
os.environ["ANALYTICS_LAB_HOME"] = str(_HOME)


@pytest.fixture(scope="session", autouse=True)
def datasets():
    from analytics_lab.data.generate import build_all

    build_all()
    yield _HOME


@pytest.fixture()
def store(tmp_path):
    from analytics_lab.progress.store import ProgressStore

    return ProgressStore(tmp_path / "progress.db")


@pytest.fixture(scope="session")
def rscript():
    from analytics_lab.capabilities import find_rscript

    return find_rscript()
