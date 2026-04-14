"""Headless UI smoke tests with Streamlit's AppTest: every page renders without exceptions."""

import pytest
from streamlit.testing.v1 import AppTest

from analytics_lab.curriculum import lessons_for
from analytics_lab.ui.pages.assessment_center import SECTIONS as ASSESS_SECTIONS
from analytics_lab.ui.pages.practice_lab import SECTIONS as PRACTICE_SECTIONS

PAGES = {
    "dashboard": "from analytics_lab.ui.pages import dashboard as m; m.render()",
    "learning_path": "from analytics_lab.ui.pages import learning_path as m; m.render()",
    "capstones": "from analytics_lab.ui.pages import capstones as m; m.render()",
    "progress": "from analytics_lab.ui.pages import progress as m; m.render()",
    "settings": "from analytics_lab.ui.pages import settings_help as m; m.render()",
}


def _app(code: str, **state) -> AppTest:
    at = AppTest.from_string(code, default_timeout=180)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


def test_full_app_starts():
    at = AppTest.from_file("../app.py", default_timeout=180)
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]


@pytest.mark.parametrize("page", list(PAGES))
def test_page_renders(page):
    _app(PAGES[page])


@pytest.mark.parametrize("module", ["descriptive", "diagnostic", "predictive", "prescriptive", "visualization"])
def test_every_lesson_renders(module):
    for lesson in lessons_for(module):
        _app(f"from analytics_lab.ui.pages.module import render_module; render_module('{module}')", **{f"lesson_sel_{module}": lesson.id})


@pytest.mark.parametrize("section", PRACTICE_SECTIONS)
def test_practice_sections(section):
    _app("from analytics_lab.ui.pages import practice_lab as m; m.render()", practice_tab=section)


@pytest.mark.parametrize("section", ASSESS_SECTIONS)
def test_assessment_sections(section):
    _app("from analytics_lab.ui.pages import assessment_center as m; m.render()", assess_tab=section)


def test_quiz_flow_immediate_feedback():
    at = _app("from analytics_lab.ui.pages import assessment_center as m; m.render()", assess_tab="Quiz")
    next(b for b in at.button if "Start quiz" in str(b.label)).click().run()
    quiz = at.session_state["quiz"]
    assert len(quiz["qids"]) == 10
    radios = [r for r in at.radio if r.key and r.key.endswith("_radio")]
    if radios:
        radios[0].set_value(radios[0].options[0]).run()
    else:
        at.checkbox[0].check().run()
    next(b for b in at.button if "Check answer" in str(b.label)).click().run()
    assert at.session_state["quiz"]["checked"] == [quiz["qids"][0]]
    assert not at.exception


def test_sql_exercise_submit_through_ui():
    code = ("from analytics_lab.assessment.bank import EXERCISES_BY_ID\n"
            "from analytics_lab.ui.components.exercise import render_exercise\n"
            "render_exercise(EXERCISES_BY_ID['ex_sql_ds1_headline'], prefix='t')")
    at = _app(code)
    ex_key = "ex_t_ex_sql_ds1_headline_code"
    from analytics_lab.assessment.bank import EXERCISES_BY_ID

    at.text_area(key=ex_key).set_value(EXERCISES_BY_ID["ex_sql_ds1_headline"].solution).run()
    next(b for b in at.button if b.label == "Submit").click().run()
    assert not at.exception
    assert any("Passed" in s.value for s in at.success)
