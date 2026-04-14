"""Curriculum registry: all lessons across the five modules."""

from __future__ import annotations

from analytics_lab.curriculum import descriptive, diagnostic, predictive, prescriptive, visualization
from analytics_lab.models import LEVELS, Lesson

LESSONS: list[Lesson] = sorted(
    descriptive.LESSONS + diagnostic.LESSONS + predictive.LESSONS + prescriptive.LESSONS + visualization.LESSONS,
    key=lambda lesson: lesson.order,
)
LESSONS_BY_ID: dict[str, Lesson] = {lesson.id: lesson for lesson in LESSONS}


def lessons_for(module: str) -> list[Lesson]:
    return [lesson for lesson in LESSONS if lesson.module == module]


def learning_path() -> list[Lesson]:
    """Recommended order: by level (Beginner -> Professional), then module order."""
    return sorted(LESSONS, key=lambda lesson: (LEVELS.index(lesson.level), lesson.order))


def get_lesson(lesson_id: str) -> Lesson | None:
    return LESSONS_BY_ID.get(lesson_id)
