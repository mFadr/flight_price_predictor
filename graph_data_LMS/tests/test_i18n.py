"""Czech language layer and dark theme: complete coverage, consistent placeholders, safe switching, unchanged grading."""

import ast
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from analytics_lab import i18n
from analytics_lab.assessment.bank import EXERCISES, EXERCISES_BY_ID, QUESTIONS
from analytics_lab.assessment.capstones import CAPSTONES
from analytics_lab.assessment.cases import CASES_BY_ID
from analytics_lab.curriculum import LESSONS, lessons_for
from analytics_lab.ui.pages.assessment_center import SECTIONS as ASSESS_SECTIONS
from analytics_lab.ui.pages.practice_lab import SECTIONS as PRACTICE_SECTIONS

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = re.compile(r"\{[^{}]*\}")


@pytest.fixture()
def czech():
    i18n.apply_language("cs")
    yield
    i18n.apply_language("en")


def _ui_literals() -> set[str]:
    found = set()
    for f in [ROOT / "app.py", *(ROOT / "analytics_lab").glob("**/*.py")]:
        if "i18n" in f.parts:
            continue
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8-sig"))):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "t" and n.args:
                if isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                    found.add(n.args[0].value)
    return found


def test_every_interface_string_has_a_czech_translation():
    catalog = i18n._ui_catalog()
    missing = sorted(s for s in _ui_literals() if s not in catalog)
    assert not missing, missing


def test_translations_keep_placeholders():
    for en, cs in i18n._ui_catalog().items():
        assert sorted(PLACEHOLDER.findall(en)) == sorted(PLACEHOLDER.findall(cs)), en


def test_t_is_identity_in_english():
    assert i18n.get_lang() == "en"
    assert i18n.t("Run") == "Run"
    assert i18n.t("{n} result(s)", n=3) == "3 result(s)"


def test_all_content_is_translated(czech):
    def untranslated(items, field):
        return [x.id for x in items if getattr(x, field).isascii()]

    assert not untranslated(LESSONS, "concept")
    assert not untranslated(QUESTIONS, "stem")
    assert not untranslated(EXERCISES, "business_question")
    assert not untranslated(CASES_BY_ID.values(), "scenario")
    assert not untranslated(CAPSTONES, "brief")
    topics = {q.topic for q in QUESTIONS}
    assert all(i18n.t(tp) != tp or tp in ("EOQ", "Drift", "R-squared", "Monte Carlo") for tp in topics)


def test_switching_back_restores_english_exactly():
    before = [(q.stem, [(o.text, o.why) for o in q.options]) for q in QUESTIONS]
    codes = {e.id: [c.code for c in e.checks] for e in EXERCISES}
    i18n.apply_language("cs")
    assert QUESTIONS[0].stem != before[0][0]
    i18n.apply_language("en")
    assert [(q.stem, [(o.text, o.why) for o in q.options]) for q in QUESTIONS] == before
    assert {e.id: [c.code for c in e.checks] for e in EXERCISES} == codes


def test_answer_keys_and_check_logic_unchanged(czech):
    i18n.apply_language("en")
    keys = {q.id: q.correct_keys for q in QUESTIONS}
    sols = {e.id: (e.solution, e.starter_code, len(e.checks)) for e in EXERCISES}
    i18n.apply_language("cs")
    assert {q.id: q.correct_keys for q in QUESTIONS} == keys
    assert {e.id: (e.solution, e.starter_code, len(e.checks)) for e in EXERCISES} == sols
    for e in EXERCISES:
        for c in e.checks:
            if e.language == "python":
                ast.parse(c.code)  # translated assert messages keep the check valid Python


def test_python_exercise_grades_in_czech(czech):
    from analytics_lab.assessment.grading import grade_exercise
    from analytics_lab.execution.runners import RunSettings

    ex = EXERCISES_BY_ID["ex_py_dg1_quality"]
    good = grade_exercise(ex, ex.solution, RunSettings(timeout=60))
    assert good.passed, good.summary
    bad = grade_exercise(ex, ex.starter_code, RunSettings(timeout=60))
    assert not bad.passed
    assert "kontrol" in bad.summary  # Czech summary text


def _run(code: str) -> AppTest:
    at = AppTest.from_string("from analytics_lab.i18n import apply_language\napply_language('cs')\n" + code, default_timeout=180)
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


@pytest.mark.parametrize("page", ["dashboard", "learning_path", "capstones", "progress", "settings_help"])
def test_pages_render_in_czech(page, czech):
    _run(f"from analytics_lab.ui.pages import {page} as m; m.render()")


@pytest.mark.parametrize("module", ["descriptive", "diagnostic", "predictive", "prescriptive", "visualization"])
def test_lessons_render_in_czech(module, czech):
    for lesson in lessons_for(module):
        at = AppTest.from_string(
            "from analytics_lab.i18n import apply_language\napply_language('cs')\n"
            f"from analytics_lab.ui.pages.module import render_module; render_module('{module}')", default_timeout=180)
        at.session_state[f"lesson_sel_{module}"] = lesson.id
        at.run()
        assert not at.exception, (lesson.id, [str(e.value) for e in at.exception])


@pytest.mark.parametrize("section", PRACTICE_SECTIONS)
def test_practice_sections_in_czech(section, czech):
    at = AppTest.from_string("from analytics_lab.i18n import apply_language\napply_language('cs')\n"
                             "from analytics_lab.ui.pages import practice_lab as m; m.render()", default_timeout=180)
    at.session_state["practice_tab"] = section
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]


@pytest.mark.parametrize("section", ASSESS_SECTIONS)
def test_assessment_sections_in_czech(section, czech):
    at = AppTest.from_string("from analytics_lab.i18n import apply_language\napply_language('cs')\n"
                             "from analytics_lab.ui.pages import assessment_center as m; m.render()", default_timeout=180)
    at.session_state["assess_tab"] = section
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]


def test_full_app_in_czech_and_dark(store):
    from analytics_lab.ui import state

    s = state.store()
    s.set_setting("language", "cs")
    s.set_setting("theme", "dark")
    try:
        at = AppTest.from_file("../app.py", default_timeout=180)
        at.run()
        assert not at.exception, [str(e.value) for e in at.exception]
        assert at.selectbox(key="ui_language").value == "cs"
        assert at.toggle(key="ui_dark").value is True
        from streamlit import config

        assert config.get_option("theme.base") == "dark"
        at.toggle(key="ui_dark").set_value(False).run()
        assert s.get_setting("theme") == "light"
        assert config.get_option("theme.base") == "light"
    finally:
        s.set_setting("language", "en")
        s.set_setting("theme", "light")
        i18n.apply_language("en")
