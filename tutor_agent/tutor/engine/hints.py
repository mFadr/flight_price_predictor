"""Graduated assistance ladder and hint/solution consistency checks."""

from __future__ import annotations

import re

from tutor.domain import AnswerType, Exercise

HINT_LEVELS = {
    1: "Small hint",
    2: "Conceptual reminder",
    3: "Suggested next step",
    4: "Partially worked solution",
    5: "Complete worked solution",
}
MAX_LEVEL = 5


def _norm(s: str) -> str:
    return re.sub(r"[\s$*]", "", s.lower())


def answer_tokens(ex: Exercise) -> list[str]:
    """Strings whose presence in a hint would give the final answer away."""
    if ex.answer_type == AnswerType.MULTIPLE_CHOICE and ex.correct_choice is not None and ex.choices:
        return [_norm(ex.choices[ex.correct_choice])] if len(ex.choices[ex.correct_choice]) > 3 else []
    if ex.answer_type in (AnswerType.CODE, AnswerType.SHORT_TEXT, AnswerType.PROOF):
        return []
    ans = ex.expected_answer.strip()
    if not ans or len(ans) > 40:
        return []
    toks = [_norm(ans)]
    # "x = 4" -> also "x=4"; plain value "4" is too generic to search for alone unless multi-char
    if "=" in ans:
        rhs = _norm(ans.split("=")[-1])
        toks.append(f"{_norm(ex.variable)}={rhs}")
    return [t for t in toks if len(t) >= 2]


def leaks_answer(text: str, ex: Exercise) -> bool:
    body = _norm(text)
    for tok in answer_tokens(ex):
        if tok and tok in body:
            return True
    # e.g. expected "4" and hint says "x = 4"
    ans = _norm(ex.expected_answer.split("=")[-1]) if ex.expected_answer else ""
    if ans and re.search(rf"{re.escape(_norm(ex.variable))}=\(?{re.escape(ans)}\)?(?![0-9.])", body):
        return True
    return False


def solution_consistent(ex: Exercise) -> bool:
    """The worked solution should arrive at the expected answer (best-effort textual check)."""
    if ex.answer_type in (AnswerType.CODE, AnswerType.SHORT_TEXT, AnswerType.PROOF, AnswerType.MULTIPLE_CHOICE):
        return True
    if not ex.solution_explanation or not ex.expected_answer:
        return False
    sol = _norm(ex.solution_explanation)
    ans = ex.expected_answer
    parts = [p for p in re.split(r"[,;]|\bor\b|\band\b", ans.split("=")[-1] if ans.count("=") == 1 else ans) if p.strip()]
    return all(_norm(p) in sol for p in parts) if parts else False


def partial_solution(ex: Exercise) -> str:
    """First part of the worked solution, stopping before the final result."""
    text = ex.solution_explanation.strip()
    steps = [s for s in re.split(r"\n+|(?<=[.!?])\s+(?=[A-Z0-9])", text) if s.strip()]
    if len(steps) <= 1:
        return ""
    keep = steps[: max(1, len(steps) // 2)]
    keep = [s for s in keep if not leaks_answer(s, ex)] or keep[:1]
    return "\n".join(keep) + "\n\n*…try to finish the remaining steps yourself.*"


def stored_hint(ex: Exercise, level: int) -> str | None:
    """Return a pre-generated, non-leaking hint for ``level`` (1-3) if available."""
    if level <= 3 and len(ex.hints) >= level:
        h = ex.hints[level - 1]
        if h.strip() and not leaks_answer(h, ex):
            return h
    if level == 4:
        p = partial_solution(ex)
        return p or None
    if level == 5:
        return ex.solution_explanation or None
    return None
