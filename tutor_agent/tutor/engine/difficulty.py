"""Adaptive difficulty policy.

Never changes the level because of a single answer. Uses only attempts made
since the last level change. A level chosen by the student (``level_locked``)
is respected; the engine then only *suggests* changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from tutor.domain import Attempt, Correctness, ErrorCategory


@dataclass
class LevelDecision:
    new_level: int
    direction: int  # +1 / -1
    reason: str


def _ok(a: Attempt) -> bool:
    ev = a.evaluation
    return bool(ev and ev.correctness == Correctness.CORRECT and ev.score >= 0.8)


def _bad(a: Attempt) -> bool:
    ev = a.evaluation
    return bool(ev and ev.correctness == Correctness.INCORRECT)


def decide(level: int, attempts: list[Attempt]) -> LevelDecision | None:
    """``attempts``: chronological, only those since the last level change."""
    evaluated = [a for a in attempts if a.evaluation and a.evaluation.correctness != Correctness.INSUFFICIENT_EVIDENCE]
    if len(evaluated) < 2:
        return None
    last3 = evaluated[-3:]

    # Increase: three correct in a row with little help.
    if len(last3) == 3 and all(_ok(a) for a in last3):
        hints = sum(a.hints_used for a in last3)
        if hints <= 2 and not any(a.solution_viewed for a in last3) and level < 5:
            return LevelDecision(level + 1, +1, "three correct answers in a row with little or no help")

    if level <= 1:
        return None
    last2 = evaluated[-2:]
    # Decrease: the same conceptual mistake twice in a row.
    cats = [a.evaluation.error_category for a in last2 if a.evaluation]  # type: ignore[union-attr]
    if all(_bad(a) for a in last2) and cats[0] is not None and cats[0] == cats[1]:
        return LevelDecision(level - 1, -1, f"the same kind of mistake ({cats[0].label.lower()}) appeared twice in a row")
    # Decrease: mostly failing while relying heavily on hints / solutions.
    if len(last3) == 3 and sum(_bad(a) for a in last3) >= 2:
        heavy = sum(a.hints_used for a in last3) >= 4 or sum(a.solution_viewed for a in last3) >= 2
        if heavy:
            return LevelDecision(level - 1, -1, "two of the last three answers were incorrect despite several hints")
    return None


CONCEPTUAL_CATEGORIES = {ErrorCategory.CONCEPTUAL, ErrorCategory.FORMULA, ErrorCategory.ASSUMPTION}
