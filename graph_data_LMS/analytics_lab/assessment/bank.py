"""Registry of questions and coding exercises."""

from __future__ import annotations

import random

from analytics_lab.assessment import (
    exercises_descriptive,
    exercises_diagnostic,
    exercises_predictive,
    exercises_prescriptive,
    exercises_visualization,
    questions_descriptive,
    questions_diagnostic,
    questions_predictive,
    questions_prescriptive,
    questions_visualization,
)
from analytics_lab.models import Exercise, Question

QUESTIONS: list[Question] = (
    questions_descriptive.QUESTIONS
    + questions_diagnostic.QUESTIONS
    + questions_predictive.QUESTIONS
    + questions_prescriptive.QUESTIONS
    + questions_visualization.QUESTIONS
)
QUESTIONS_BY_ID: dict[str, Question] = {q.id: q for q in QUESTIONS}

EXERCISES: list[Exercise] = (
    exercises_descriptive.EXERCISES
    + exercises_diagnostic.EXERCISES
    + exercises_predictive.EXERCISES
    + exercises_prescriptive.EXERCISES
    + exercises_visualization.EXERCISES
)


def _register_extra() -> None:
    # Capstone exercises live with the capstones but are graded the same way.
    from analytics_lab.assessment.capstones import CAPSTONE_EXERCISES

    for ex in CAPSTONE_EXERCISES:
        if ex.id not in {e.id for e in EXERCISES}:
            EXERCISES.append(ex)


_register_extra()
EXERCISES_BY_ID: dict[str, Exercise] = {e.id: e for e in EXERCISES}


def filter_questions(modules=None, topics=None, difficulties=None, tools=None, competencies=None) -> list[Question]:
    out = QUESTIONS
    if modules:
        out = [q for q in out if q.module in modules]
    if topics:
        out = [q for q in out if q.topic in topics]
    if difficulties:
        out = [q for q in out if q.difficulty in difficulties]
    if tools:
        out = [q for q in out if q.tool in tools]
    if competencies:
        out = [q for q in out if q.competency in competencies]
    return out


def sample_questions(pool: list[Question], n: int, avoid: set[str] | None = None, prefer: set[str] | None = None, rng: random.Random | None = None) -> list[Question]:
    """Random sample that prefers previously missed questions and avoids recently seen ones."""
    rng = rng or random.Random()
    avoid, prefer = avoid or set(), prefer or set()
    preferred = [q for q in pool if q.id in prefer and q.id not in avoid]
    fresh = [q for q in pool if q.id not in avoid and q.id not in prefer]
    seen = [q for q in pool if q.id in avoid]
    rng.shuffle(preferred)
    rng.shuffle(fresh)
    rng.shuffle(seen)
    take = preferred[: max(1, n // 3)] if preferred else []
    rest = [q for q in fresh + preferred[len(take):] + seen if q not in take]
    chosen = (take + rest)[:n]
    rng.shuffle(chosen)
    return chosen


def stratified_sample(n_per_module: int, rng: random.Random | None = None) -> list[Question]:
    """Sample across modules and difficulty for the final competency assessment."""
    rng = rng or random.Random()
    out: list[Question] = []
    for module in ["descriptive", "diagnostic", "predictive", "prescriptive", "visualization"]:
        pool = [q for q in QUESTIONS if q.module == module]
        harder = [q for q in pool if q.difficulty in ("Advanced", "Professional")]
        easier = [q for q in pool if q not in harder]
        rng.shuffle(harder)
        rng.shuffle(easier)
        k_hard = max(1, n_per_module // 2)
        out += harder[:k_hard] + easier[: n_per_module - k_hard]
    rng.shuffle(out)
    return out


def exercises_for(module: str | None = None, language: str | None = None) -> list[Exercise]:
    out = EXERCISES
    if module:
        out = [e for e in out if e.module == module]
    if language:
        out = [e for e in out if e.language == language]
    return out


FINAL_EXERCISES = [
    "ex_sql_ds7_monthly_kpis",
    "ex_py_dg4_simpson",
    "ex_py_pr3_threshold",
    "ex_py_ps5_budget",
    "ex_py_vz4_fix",
]
