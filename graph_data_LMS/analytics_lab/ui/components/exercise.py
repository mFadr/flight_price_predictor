"""Interactive coding exercise: editor, run, submit, progressive hints, solution reveal."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics_lab.assessment.grading import GradeResult, feedback_dict, grade_exercise
from analytics_lab.capabilities import R_INSTALL_HELP
from analytics_lab.execution.runners import run_python, run_r, run_sql
from analytics_lab.i18n import t
from analytics_lab.models import Exercise
from analytics_lab.ui import state
from analytics_lab.ui.components.outputs import level_badge, schema_panel, show_python_run, show_sql_run

LANG_LABEL = {"sql": "SQL (DuckDB)", "python": "Python", "r": "R"}


def _k(ex: Exercise, prefix: str, name: str) -> str:
    return f"ex_{prefix}_{ex.id}_{name}"


def render_exercise(ex: Exercise, prefix: str = "main", on_pass=None, compact: bool = False) -> GradeResult | None:
    """Render an exercise. ``on_pass(grade)`` is called once when a submission passes."""
    store = state.store()
    code_key = _k(ex, prefix, "code")
    hints_key = _k(ex, prefix, "hints")
    sol_key = _k(ex, prefix, "solution_viewed")
    grade_key = _k(ex, prefix, "grade")
    run_key = _k(ex, prefix, "run")
    st.session_state.setdefault(code_key, ex.starter_code)
    st.session_state.setdefault(hints_key, 0)
    st.session_state.setdefault(sol_key, False)

    history = store.exercise_attempts(ex.id)
    best = history["score"].max() if len(history) else None

    if not compact:
        st.markdown(f"#### {ex.title}")
    badges = f"{level_badge(ex.difficulty)} :gray-background[{LANG_LABEL.get(ex.language, ex.language)}] :gray-background[{ex.topic}]"
    if best is not None:
        badges += (f" :green-background[{t('best {b:.0f}/100', b=best)}]" if history["passed"].max() else f" :orange-background[{t('best {b:.0f}/100', b=best)}]")
    st.markdown(badges)
    st.markdown(t("**Business question.**") + f" {ex.business_question}")

    with st.expander(t("Task requirements, expected output and scoring"), expanded=not compact):
        st.markdown("\n".join(f"- {r}" for r in ex.requirements))
        st.markdown(t("**Expected output:**") + f" {ex.expected_output}")
        if ex.sample_output:
            st.code(ex.sample_output, language="text")
        if ex.language == "sql":
            st.markdown(t("**How it is assessed:** your result set is compared with the expected data - column names (case-insensitive), "
                          "row count and values (numeric tolerance {tol}){order}. Any query that returns the right data earns full marks.",
                          tol=ex.float_tol, order=t(", and row order") if ex.order_matters else t("; row order is ignored")))
        elif ex.visible_tests:
            st.markdown(t("**Automated checks** (the test code itself is hidden):") + "\n" + "\n".join(f"- {v}" for v in ex.visible_tests))
        if ex.rubric:
            st.dataframe(pd.DataFrame(ex.rubric, columns=[t("Criterion"), t("Points")]), hide_index=True, width="stretch")
    if ex.tables:
        with st.expander(t("Dataset & schema")):
            if ex.preload:
                st.markdown(t("Pre-loaded variables: ") + ", ".join(f"`{v}` = `{t}`" for v, t in ex.preload.items()))
            if ex.language == "sql" and ex.search_path:
                st.markdown(t("Default schema: `{s}` - you can write `orders` instead of `{s}.orders`.", s=ex.search_path))
            schema_panel(ex.tables)

    rscript = state.rscript()
    r_missing = ex.language == "r" and not rscript
    if r_missing:
        st.warning(t("R is not installed or not found, so this exercise cannot run. You can still read the task and the hints."))
        with st.expander(t("How to enable R")):
            st.markdown(t(R_INSTALL_HELP))

    st.text_area(t("Your {lang} code", lang=LANG_LABEL.get(ex.language, ex.language)), key=code_key, height=280 if not compact else 220,
                 help=t("Tip: Ctrl+Enter applies the edit. Each run starts fresh in a separate process."))

    c1, c2, c3, c4, c5 = st.columns(5)
    run_clicked = c1.button(t("Run"), key=_k(ex, prefix, "btn_run"), icon=":material/play_arrow:", width="stretch", disabled=r_missing)
    submit_clicked = c2.button(t("Submit"), key=_k(ex, prefix, "btn_submit"), type="primary", icon=":material/task_alt:", width="stretch", disabled=r_missing)
    n_hints = len(ex.hints)
    hint_clicked = c3.button(t("Hint ({i}/{n})", i=st.session_state[hints_key], n=n_hints), key=_k(ex, prefix, "btn_hint"), icon=":material/lightbulb:",
                             width="stretch", disabled=st.session_state[hints_key] >= n_hints)
    reset_clicked = c4.button(t("Reset"), key=_k(ex, prefix, "btn_reset"), icon=":material/restart_alt:", width="stretch")
    show_sol = c5.toggle(t("Solution"), key=_k(ex, prefix, "tgl_sol"))

    if hint_clicked:
        st.session_state[hints_key] += 1
        st.rerun()
    if reset_clicked:
        st.session_state.pop(code_key, None)
        st.session_state.pop(grade_key, None)
        st.session_state.pop(run_key, None)
        st.rerun()

    for i in range(st.session_state[hints_key]):
        st.info(t("**Hint {n}:**", n=i + 1) + f" {ex.hints[i]}", icon=":material/lightbulb:")

    code = st.session_state[code_key]
    settings = state.run_settings()
    if run_clicked:
        with st.spinner(t("Running in a separate process...")):
            if ex.language == "sql":
                st.session_state[run_key] = ("sql", run_sql(code, settings, ex.search_path))
            elif ex.language == "python":
                st.session_state[run_key] = ("python", run_python(code, settings, ex.preload, search_path=ex.search_path))
            else:
                st.session_state[run_key] = ("r", run_r(code, rscript, settings, ex.preload))
        st.session_state.pop(grade_key, None)
        store.log("code_run", ex.id, ex.language)

    if submit_clicked:
        with st.spinner(t("Grading against hidden checks...")):
            g = grade_exercise(ex, code, settings, rscript)
        st.session_state[grade_key] = g
        st.session_state.pop(run_key, None)
        if g.content_error:
            st.error(g.content_error)
        else:
            store.record_exercise(ex, g.passed, g.score, code, feedback_dict(g), st.session_state[hints_key], st.session_state[sol_key])
            if g.passed and on_pass:
                on_pass(g)
        history = store.exercise_attempts(ex.id)

    last_run = st.session_state.get(run_key)
    if last_run:
        kind, run = last_run
        with st.container(border=True):
            st.markdown(t("**Run output** (not graded)"))
            if kind == "sql":
                show_sql_run(run, _k(ex, prefix, "out"))
            else:
                show_python_run(run, _k(ex, prefix, "out"))

    g: GradeResult | None = st.session_state.get(grade_key)
    if g is not None:
        _render_grade(ex, g, prefix)

    # Solution reveal: encouraged only after an attempt.
    if show_sol:
        attempted = len(history) > 0
        if not attempted and not st.checkbox(t("I understand that looking before trying reduces learning. Show the solution anyway."),
                                             key=_k(ex, prefix, "confirm_sol")):
            st.caption(t("Submit at least one attempt to unlock the worked solution, or confirm above."))
        else:
            if not st.session_state[sol_key]:
                st.session_state[sol_key] = True
                store.log("solution_viewed", ex.id)
            with st.container(border=True):
                st.markdown(t("**Reference solution**"))
                if attempted:
                    a, b = st.columns(2)
                    a.caption(t("Your latest code"))
                    a.code(st.session_state[code_key], language="sql" if ex.language == "sql" else ex.language)
                    b.caption(t("Reference"))
                    b.code(ex.solution, language="sql" if ex.language == "sql" else ex.language)
                else:
                    st.code(ex.solution, language="sql" if ex.language == "sql" else ex.language)
                st.markdown(t("**Why it works.**") + f" {ex.explanation}")
                st.caption(t("Passing after viewing the solution is recorded as assisted (capped at 70 in your competency score). Equivalent approaches are accepted."))

    if len(history):
        with st.expander(t("Attempt history ({n})", n=len(history))):
            h = history[["attempt_id", "submitted_at", "score", "passed", "hints_used", "solution_viewed"]].copy()
            h["attempt"] = range(1, len(h) + 1)
            if len(h) > 1:
                fig = px.line(h, x="attempt", y="score", markers=True, range_y=[0, 105], height=220)
                fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, key=_k(ex, prefix, "hist_chart"))
            st.dataframe(h.drop(columns=["attempt_id"]).rename(columns=t), hide_index=True, width="stretch")
    return g


def _render_grade(ex: Exercise, g: GradeResult, prefix: str) -> None:
    with st.container(border=True):
        if g.content_error:
            st.error(g.content_error)
            return
        if g.passed:
            st.success(t("**Passed - {s:.0f}/100.**", s=g.score) + f" {g.summary}", icon=":material/check_circle:")
        else:
            st.warning(t("**Score {s:.0f}/100.**", s=g.score) + f" {g.summary}", icon=":material/error:")
        if g.error:
            st.code(g.error, language="text")
            if g.hint:
                st.info(t("**Hint:** {hint}", hint=t(g.hint)))
        for item in g.items:
            icon = ":green[✔]" if item.passed else ":red[✘]"
            msg = f" - {item.message}" if item.message and (not item.passed or ex.language == "sql") else ""
            st.markdown(f"{icon} **{t(item.name)}**{msg}")
        if g.next_step:
            st.markdown(t("**Next step:**") + f" {g.next_step}")
        if ex.language == "sql" and g.user_frame is not None:
            with st.expander(t("Your result")):
                st.dataframe(g.user_frame.head(200), hide_index=True, width="stretch")
            if not g.passed and g.expected_preview is not None:
                with st.expander(t("Expected output (first rows) - revealed after your attempt")):
                    st.dataframe(g.expected_preview, hide_index=True, width="stretch")
        if g.run is not None and ex.language != "sql":
            with st.expander(t("Program output")):
                show_python_run(g.run, _k(ex, prefix, "grade_out"))
