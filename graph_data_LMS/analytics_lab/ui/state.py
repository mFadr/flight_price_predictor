"""Session-level helpers: cached resources, settings and page navigation."""

from __future__ import annotations

import streamlit as st

from analytics_lab.capabilities import check_r, find_rscript
from analytics_lab.config import get_paths
from analytics_lab.execution.runners import RunSettings
from analytics_lab.progress.store import ProgressStore


@st.cache_resource(show_spinner=False)
def _store(path: str) -> ProgressStore:
    return ProgressStore()


def store() -> ProgressStore:
    return _store(str(get_paths().progress_db))


def settings() -> dict[str, str]:
    return store().get_settings()


def threshold() -> float:
    try:
        return float(settings()["mastery_threshold"])
    except (KeyError, ValueError):
        return 80.0


@st.cache_data(show_spinner=False, ttl=600)
def _rscript(explicit: str) -> str | None:
    return find_rscript(explicit or None)


def rscript() -> str | None:
    return _rscript(settings().get("r_executable", ""))


@st.cache_data(show_spinner=False, ttl=600)
def r_status(explicit: str):
    return check_r(explicit or None)


def run_settings() -> RunSettings:
    s = settings()
    try:
        timeout = max(3, min(300, int(float(s.get("execution_timeout", "20")))))
    except ValueError:
        timeout = 20
    return RunSettings(timeout=timeout, backend=s.get("execution_backend", "local"), docker_image=s.get("docker_image", "analytics-lab-runner:latest"), r_executable=rscript())


# --------------------------------------------------------------------------- #
# Navigation                                                                   #
# --------------------------------------------------------------------------- #
def register_pages(pages: dict) -> None:
    st.session_state["_pages"] = pages


def go(page_key: str, **state) -> None:
    """Switch to a page, optionally pre-selecting e.g. a lesson or exercise."""
    for k, v in state.items():
        st.session_state[k] = v
    pages = st.session_state.get("_pages", {})
    if page_key in pages:
        st.switch_page(pages[page_key])


def open_lesson(lesson_id: str) -> None:
    from analytics_lab.curriculum import get_lesson

    lesson = get_lesson(lesson_id)
    if lesson:
        go(lesson.module, **{f"lesson_sel_{lesson.module}": lesson_id})


def open_exercise(exercise_id: str) -> None:
    go("practice", practice_tab="Coding challenges", challenge_sel=exercise_id)


def open_capstone(capstone_id: str) -> None:
    go("capstones", capstone_sel=capstone_id)
