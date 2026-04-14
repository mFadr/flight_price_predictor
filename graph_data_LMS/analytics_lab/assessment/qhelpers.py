"""Compact constructor for question-bank entries."""

from __future__ import annotations

from analytics_lab.models import Option, Question


def q(
    id: str,
    module: str,
    topic: str,
    tool: str,
    difficulty: str,
    competency: str,
    stem: str,
    options: list[tuple[str, bool, str]],
    explanation: str,
    lesson: str | None = None,
    qtype: str | None = None,
    shuffle: bool = True,
    code: str | None = None,
) -> Question:
    opts = [Option(text, correct, why) for text, correct, why in options]
    n_correct = sum(o.correct for o in opts)
    if n_correct == 0:
        raise ValueError(f"{id}: no correct option")
    return Question(
        id=id, module=module, topic=topic, tool=tool, difficulty=difficulty, competency=competency,
        qtype=qtype or ("multi" if n_correct > 1 else "single"), stem=stem, options=opts,
        explanation=explanation, lesson=lesson, shuffle=shuffle, code=code,
    )
