"""Validate curriculum integrity and that every reference solution passes its own grader.

Usage:  python scripts/validate_content.py [exercise_id ...]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics_lab.assessment.bank import EXERCISES, EXERCISES_BY_ID, QUESTIONS, QUESTIONS_BY_ID  # noqa: E402
from analytics_lab.assessment.capstones import CAPSTONES  # noqa: E402
from analytics_lab.assessment.grading import grade_exercise  # noqa: E402
from analytics_lab.capabilities import find_rscript  # noqa: E402
from analytics_lab.curriculum import LESSONS, LESSONS_BY_ID  # noqa: E402
from analytics_lab.curriculum.competencies import BY_ID as COMP  # noqa: E402
from analytics_lab.execution.runners import RunSettings, run_python, run_sql  # noqa: E402


def check_references() -> list[str]:
    problems = []
    for lesson in LESSONS:
        for qid in lesson.knowledge_check:
            if qid not in QUESTIONS_BY_ID:
                problems.append(f"{lesson.id}: unknown question {qid}")
        for ex in (lesson.guided_exercise, lesson.challenge):
            if ex and ex not in EXERCISES_BY_ID:
                problems.append(f"{lesson.id}: unknown exercise {ex}")
        if lesson.next_lesson and lesson.next_lesson not in LESSONS_BY_ID:
            problems.append(f"{lesson.id}: unknown next lesson {lesson.next_lesson}")
        for c in lesson.competencies:
            if c not in COMP:
                problems.append(f"{lesson.id}: unknown competency {c}")
    for q in QUESTIONS:
        if q.competency not in COMP:
            problems.append(f"{q.id}: unknown competency {q.competency}")
        if q.lesson and q.lesson not in LESSONS_BY_ID:
            problems.append(f"{q.id}: unknown lesson {q.lesson}")
    for e in EXERCISES:
        for c in e.competencies:
            if c not in COMP:
                problems.append(f"{e.id}: unknown competency {c}")
    for cap in CAPSTONES:
        for m in cap.milestones:
            if m.exercise_id and m.exercise_id not in EXERCISES_BY_ID:
                problems.append(f"{cap.id}/{m.id}: unknown exercise {m.exercise_id}")
        for p in cap.prerequisites:
            if p not in LESSONS_BY_ID:
                problems.append(f"{cap.id}: unknown prerequisite {p}")
    ids = [q.id for q in QUESTIONS]
    if len(ids) != len(set(ids)):
        problems.append("duplicate question ids")
    return problems


def run_examples() -> list[str]:
    problems = []
    for lesson in LESSONS:
        for ex in [lesson.worked_example, *lesson.extra_examples]:
            if not ex.runnable:
                continue
            if ex.language == "sql":
                r = run_sql(ex.code, RunSettings(timeout=60), search_path=ex.search_path)
                if not r.ok:
                    problems.append(f"{lesson.id} example SQL: {r.error}")
            elif ex.language == "python":
                r = run_python(ex.code, RunSettings(timeout=90), preload=ex.preload)
                if not r.ok:
                    problems.append(f"{lesson.id} example Python: {r.error}")
    return problems


def run_solutions(only: list[str]) -> list[str]:
    problems = []
    rscript = find_rscript()
    for ex in EXERCISES:
        if only and ex.id not in only:
            continue
        if ex.language == "r" and not rscript:
            print(f"  skip {ex.id} (R not installed)")
            continue
        t = time.perf_counter()
        g = grade_exercise(ex, ex.solution, RunSettings(timeout=120), rscript)
        status = "PASS" if g.passed else "FAIL"
        print(f"  {status} {ex.id} ({time.perf_counter() - t:.1f}s) {g.score}")
        if not g.passed:
            detail = g.content_error or g.error or "; ".join(f"{i.name}: {i.message}" for i in g.items if not i.passed)
            problems.append(f"{ex.id}: {detail}")
    return problems


if __name__ == "__main__":
    only = sys.argv[1:]
    print(f"{len(LESSONS)} lessons, {len(QUESTIONS)} questions, {len(EXERCISES)} exercises, {len(CAPSTONES)} capstones")
    probs = check_references()
    if not only:
        print("Running worked examples...")
        probs += run_examples()
    print("Grading reference solutions...")
    probs += run_solutions(only)
    print("\n".join(probs) if probs else "ALL OK")
    sys.exit(1 if probs else 0)
