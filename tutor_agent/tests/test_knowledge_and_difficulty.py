from datetime import datetime, timedelta, timezone

from tutor.domain import (
    Attempt,
    Correctness,
    ErrorCategory,
    Evaluation,
    Evidence,
    EvidenceKind,
    MasteryState,
)
from tutor.engine import difficulty
from tutor.engine.knowledge import assess

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def ev(i, correct=True, assistance=0, kind="calculation", difficulty=3, cat=None, ex=None):
    return Evidence(subject="Mathematics", topic="Algebra", concept="linear equations", kind=EvidenceKind.ATTEMPT,
                    correct=correct, score=1.0 if correct else 0.0, assistance=assistance, exercise_kind=kind,
                    difficulty=difficulty, error_category=cat, exercise_id=ex or f"ex{i}", created=T0 + timedelta(minutes=i))


def st(evidence):
    return assess(evidence, "Mathematics", "Algebra", "linear equations")


def test_no_evidence_is_not_assessed():
    assert st([]).state == MasteryState.NOT_ASSESSED


def test_explained_only_is_introduced_not_weakness():
    e = Evidence(subject="M", topic="A", concept="c", kind=EvidenceKind.INTRODUCED)
    s = st([e])
    assert s.state == MasteryState.INTRODUCED and s.certainty == "low"


def test_single_easy_correct_answer_is_not_mastery():
    s = st([ev(0, difficulty=1)])
    assert s.state == MasteryState.DEVELOPING and s.certainty == "low"


def test_repeated_same_format_not_enough():
    s = st([ev(i) for i in range(4)])  # same kind and level every time
    assert s.state == MasteryState.DEVELOPING
    assert "format" in s.rationale


def test_demonstrated_requires_variety_and_independence():
    s = st([ev(0), ev(1, kind="multiple_choice"), ev(2, difficulty=4)])
    assert s.state == MasteryState.DEMONSTRATED


def test_hint_heavy_successes_do_not_count_as_independent():
    s = st([ev(0, assistance=3), ev(1, assistance=3, kind="multiple_choice"), ev(2, assistance=5, difficulty=4)])
    assert s.state == MasteryState.DEVELOPING and s.independent_successes == 0


def test_same_exercise_repeated_does_not_count_thrice():
    s = st([ev(0, ex="A"), ev(1, ex="A", kind="multiple_choice"), ev(2, ex="A", difficulty=4)])
    assert s.state == MasteryState.DEVELOPING


def test_needs_revision_after_later_failures():
    good = [ev(0), ev(1, kind="multiple_choice"), ev(2, difficulty=4), ev(3)]
    s = st(good + [ev(4, correct=False), ev(5, correct=False)])
    assert s.state == MasteryState.NEEDS_REVISION


def test_recurring_errors_detected():
    e = [ev(i, correct=False, cat=ErrorCategory.SIGN_ARITHMETIC) for i in range(4)]
    s = st(e)
    assert ErrorCategory.SIGN_ARITHMETIC in s.recurring_errors
    assert s.state == MasteryState.NEEDS_REVISION


def test_override_is_respected_but_evidence_kept():
    s = assess([ev(0)], "M", "A", "c", override=(MasteryState.DEMONSTRATED, "I know this from school"))
    assert s.state == MasteryState.DEMONSTRATED and s.overridden and "Evidence-based estimate" in s.rationale


# ----------------------------------------------------------------- difficulty

def att(i, correctness, hints=0, cat=None, solution=False):
    return Attempt(exercise_id=f"e{i}", session_id="s", answer="", hints_used=hints, solution_viewed=solution,
                   evaluation=Evaluation(correctness=correctness, score=1.0 if correctness == Correctness.CORRECT else 0.0,
                                         error_category=cat))


def test_single_incorrect_never_changes_level():
    assert difficulty.decide(3, [att(0, Correctness.INCORRECT)]) is None
    assert difficulty.decide(3, [att(0, Correctness.CORRECT), att(1, Correctness.INCORRECT)]) is None


def test_three_independent_correct_increase():
    d = difficulty.decide(3, [att(i, Correctness.CORRECT) for i in range(3)])
    assert d and d.new_level == 4


def test_correct_with_many_hints_does_not_increase():
    assert difficulty.decide(3, [att(i, Correctness.CORRECT, hints=2) for i in range(3)]) is None


def test_same_conceptual_mistake_twice_decreases():
    c = ErrorCategory.CONCEPTUAL
    d = difficulty.decide(3, [att(0, Correctness.INCORRECT, cat=c), att(1, Correctness.INCORRECT, cat=c)])
    assert d and d.new_level == 2


def test_different_mistakes_do_not_decrease_without_hint_reliance():
    d = difficulty.decide(3, [att(0, Correctness.INCORRECT, cat=ErrorCategory.CONCEPTUAL),
                              att(1, Correctness.INCORRECT, cat=ErrorCategory.UNITS)])
    assert d is None


def test_hint_reliance_with_failures_decreases():
    d = difficulty.decide(3, [att(0, Correctness.INCORRECT, hints=2), att(1, Correctness.CORRECT, hints=1),
                              att(2, Correctness.INCORRECT, hints=2)])
    assert d and d.direction == -1
