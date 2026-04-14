"""Competency scoring, mastery rules and adaptive recommendations."""

from datetime import datetime, timedelta

from analytics_lab.assessment.bank import EXERCISES, QUESTIONS
from analytics_lab.competency import completion_summary, compute_competencies, recommend


def _answer(store, comp, n, correct):
    qs = [q for q in QUESTIONS if q.competency == comp][:n]
    a = store.start_quiz("practice", len(qs))
    for q in qs:
        store.record_response(a, q, ["0"], correct)
    store.finish_quiz(a, len(qs) if correct else 0)


def _by_id(store, thr=80):
    return {s.id: s for s in compute_competencies(store, thr)}


def test_no_evidence_means_not_started(store):
    assert all(s.status == "Not started" for s in compute_competencies(store))


def test_quiz_only_cannot_master_practical_competency(store):
    _answer(store, "sql_window", 3, True)
    s = _by_id(store)["sql_window"]
    assert s.knowledge == 100 and s.practical is None
    assert s.status == "Needs practical evidence"


def test_practical_evidence_enables_mastery(store):
    _answer(store, "sql_window", 3, True)
    tagged = [e for e in EXERCISES if "sql_window" in e.competencies]
    for e in tagged[: (len(tagged) + 1) // 2 + 1]:
        store.record_exercise(e, True, 100, "code", {})
    s = _by_id(store)["sql_window"]
    assert s.practical == 100 and s.coverage >= 0.5 and s.status == "Mastered"


def test_assisted_pass_is_capped(store):
    e = next(e for e in EXERCISES if "sql_basics" in e.competencies)
    store.record_exercise(e, True, 100, "code", {}, solution_viewed=True)
    assert _by_id(store)["sql_basics"].practical == 70


def test_threshold_is_configurable(store):
    _answer(store, "chart_selection", 3, True)
    e = next(e for e in EXERCISES if "chart_selection" in e.competencies)
    store.record_exercise(e, False, 60, "code", {})
    lo, hi = _by_id(store, 50)["chart_selection"], _by_id(store, 95)["chart_selection"]
    assert lo.score == hi.score
    assert lo.status in ("Mastered", "Needs more evidence") and hi.status in ("Developing", "Needs work")


def test_first_recommendation_for_new_learner(store):
    recs = recommend(store)
    assert len(recs) == 1 and recs[0].target == "ds1"


def test_weak_foundation_triggers_revision(store):
    _answer(store, "sql_basics", 4, False)
    recs = recommend(store)
    assert any(r.kind == "lesson" and "fundamentals" in r.title.lower() for r in recs)
    assert all(r.reason for r in recs)


def test_repeated_failures_on_exercise(store):
    e = next(e for e in EXERCISES if e.lesson == "ds3")
    store.record_exercise(e, False, 20, "x", {})
    store.record_exercise(e, False, 40, "y", {})
    recs = recommend(store, limit=10)
    assert any(r.target == "ds3" for r in recs)


def test_spaced_review_of_old_mistakes(store):
    _answer(store, "kpi_reporting", 2, False)
    recs = recommend(store, now=datetime.now() + timedelta(days=4), limit=10)
    assert any(r.kind == "quiz" for r in recs)


def test_capstone_recommended_when_prerequisites_done(store):
    for lid in ["ps1", "ps4", "ps5"]:
        store.complete_lesson(lid)
    recs = recommend(store, limit=10)
    assert any(r.kind == "capstone" and r.target == "cap4" for r in recs)


def test_completion_summary(store):
    store.complete_lesson("ds1")
    s = completion_summary(store)
    assert s["lessons_done"] == 1 and 0 < s["completion_pct"] < 5
