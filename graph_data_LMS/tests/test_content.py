"""Curriculum integrity and that every reference solution passes its own automated checks."""

import pytest

from analytics_lab.assessment.bank import EXERCISES, EXERCISES_BY_ID, QUESTIONS, QUESTIONS_BY_ID
from analytics_lab.assessment.capstones import CAPSTONES
from analytics_lab.assessment.cases import CASES
from analytics_lab.assessment.grading import grade_exercise
from analytics_lab.curriculum import LESSONS, LESSONS_BY_ID, lessons_for
from analytics_lab.curriculum.competencies import BY_ID as COMP
from analytics_lab.execution.runners import RunSettings
from analytics_lab.models import LEVELS, MODULES


def test_volume_of_content():
    assert len(LESSONS) >= 30
    assert len(QUESTIONS) >= 100
    assert len(EXERCISES) >= 40
    assert len(CAPSTONES) >= 5
    assert len(CASES) >= 6
    assert {e.language for e in EXERCISES} == {"sql", "python", "r"}


@pytest.mark.parametrize("module", list(MODULES))
def test_each_module_has_all_levels_and_lessons(module):
    lessons = lessons_for(module)
    assert len(lessons) >= 5
    assert {lesson.level for lesson in lessons} == set(LEVELS)


def test_lessons_have_full_structure_and_valid_references():
    for lesson in LESSONS:
        assert lesson.objectives and lesson.concept.strip() and lesson.business_context.strip() and lesson.summary, lesson.id
        assert lesson.worked_example.code.strip() and lesson.worked_example.explanation.strip(), lesson.id
        assert lesson.knowledge_check, lesson.id
        assert lesson.guided_exercise or lesson.tool_workshop, f"{lesson.id} has no practice activity"
        for qid in lesson.knowledge_check:
            assert qid in QUESTIONS_BY_ID, (lesson.id, qid)
        for ex in (lesson.guided_exercise, lesson.challenge):
            assert ex is None or ex in EXERCISES_BY_ID, (lesson.id, ex)
        assert lesson.next_lesson is None or lesson.next_lesson in LESSONS_BY_ID
        assert all(c in COMP for c in lesson.competencies)


def test_questions_are_well_formed():
    ids = set()
    for q in QUESTIONS:
        assert q.id not in ids
        ids.add(q.id)
        assert len(q.options) == 4, q.id
        assert q.correct_keys, q.id
        assert q.qtype == ("multi" if len(q.correct_keys) > 1 else "single"), q.id
        assert all(o.why.strip() for o in q.options), f"{q.id}: every option needs an explanation"
        assert q.competency in COMP and q.difficulty in LEVELS and q.module in MODULES


def test_exercises_are_well_formed():
    for e in EXERCISES:
        assert e.requirements and e.hints and e.solution.strip() and e.explanation.strip(), e.id
        assert all(c in COMP for c in e.competencies), e.id
        if e.language in ("python", "r"):
            assert e.checks, f"{e.id}: needs automated checks"


def test_capstones_reference_existing_exercises():
    for cap in CAPSTONES:
        assert cap.milestones and cap.evaluation and cap.strong_example.strip()
        for m in cap.milestones:
            assert m.kind in ("exercise", "text", "checklist", "case")
            if m.kind == "exercise":
                assert m.exercise_id in EXERCISES_BY_ID


@pytest.mark.parametrize("ex_id", [e.id for e in EXERCISES])
def test_reference_solution_passes(ex_id, rscript):
    ex = EXERCISES_BY_ID[ex_id]
    if ex.language == "r" and not rscript:
        pytest.skip("R not installed")
    g = grade_exercise(ex, ex.solution, RunSettings(timeout=120), rscript)
    assert g.content_error is None, g.content_error
    assert g.passed, [(i.name, i.message) for i in g.items if not i.passed] or g.error


@pytest.mark.parametrize("ex_id", [e.id for e in EXERCISES if e.language != "r"])
def test_starter_code_does_not_pass(ex_id):
    """Starter code must not already satisfy the checks (otherwise the exercise teaches nothing)."""
    ex = EXERCISES_BY_ID[ex_id]
    g = grade_exercise(ex, ex.starter_code, RunSettings(timeout=60))
    assert not g.passed
