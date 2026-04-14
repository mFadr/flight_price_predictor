"""Generic page for one of the five learning modules."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analytics_lab.assessment.bank import EXERCISES_BY_ID, exercises_for
from analytics_lab.capabilities import R_INSTALL_HELP
from analytics_lab.curriculum import get_lesson, lessons_for
from analytics_lab.curriculum.competencies import BY_ID as COMP
from analytics_lab.execution.runners import run_python, run_r, run_sql
from analytics_lab.i18n import t
from analytics_lab.models import LEVELS, MODULE_QUESTIONS, MODULE_TOOLS, MODULES, Lesson, WorkedExample
from analytics_lab.ui import state
from analytics_lab.ui.components.exercise import render_exercise
from analytics_lab.ui.components.mcq import knowledge_check
from analytics_lab.ui.components.outputs import level_badge, show_python_run, show_sql_run
from analytics_lab.ui.components.workshops import WORKSHOPS, render_workshop

LANG = {"sql": "sql", "python": "python", "r": "r", "dax": "text", "excel": "text", "text": "text"}


def render_module(module: str) -> None:
    store = state.store()
    lessons = lessons_for(module)
    done = store.completed_lessons()
    n_done = sum(lesson.id in done for lesson in lessons)

    st.title(MODULES[module])
    st.markdown(t("**Core question:** *{q}*  \n**Primary tools:** {tools}", q=MODULE_QUESTIONS[module], tools=", ".join(MODULE_TOOLS[module])))
    st.progress(n_done / len(lessons), text=t("{done} of {total} lessons completed", done=n_done, total=len(lessons)))

    sel_key = f"lesson_sel_{module}"
    ids = [lesson.id for lesson in lessons]
    if st.session_state.get(sel_key) not in ids:
        st.session_state[sel_key] = next((i for i in ids if i not in done), ids[0])

    tab_lessons, tab_ex, tab_tools = st.tabs([t("Lessons"), t("All module exercises"), t("Tool workshops")])
    with tab_lessons:
        def fmt(lid: str) -> str:
            lesson = get_lesson(lid)
            mark = "✅ " if lid in done else ""
            return f"{mark}{lesson.order:02d}. {lesson.title} · {t(lesson.level)}"

        st.selectbox(t("Choose a lesson"), ids, key=sel_key, format_func=fmt)
        render_lesson(get_lesson(st.session_state[sel_key]))
    with tab_ex:
        _module_exercises(module)
    with tab_tools:
        relevant = [w for w, (_, m) in WORKSHOPS.items() if m == module] or []
        if module == "descriptive":
            relevant = ["excel_workbook", "powerbi_model"]
        if not relevant:
            st.info(t("This module's practice runs in code. Tool workshops live in Descriptive (Excel, Power BI) and Visualization (Tableau, Looker Studio, critique)."))
        for w in relevant:
            with st.expander(t(WORKSHOPS[w][0]), expanded=len(relevant) == 1):
                render_workshop(w, key=f"mod_{module}_{w}")


def _module_exercises(module: str) -> None:
    exs = exercises_for(module)
    summary = state.store().exercise_summary()
    best = dict(zip(summary["exercise_id"], summary["best_score"])) if not summary.empty else {}
    passed = set(summary[summary["passed"] == 1]["exercise_id"]) if not summary.empty else set()
    rows = [{t("Exercise"): e.title, t("Language"): e.language.upper(), t("Level"): t(e.difficulty), t("Type"): t(e.kind), t("Topic"): e.topic,
             t("Best"): best.get(e.id), t("Status"): t("✅ passed") if e.id in passed else (t("attempted") if e.id in best else "")} for e in exs]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    pick = st.selectbox(t("Open an exercise"), [e.id for e in exs], format_func=lambda i: EXERCISES_BY_ID[i].title, key=f"modex_{module}")
    with st.container(border=True):
        render_exercise(EXERCISES_BY_ID[pick], prefix=f"mod_{module}")


def _run_example(ex: WorkedExample, key: str) -> None:
    if not ex.runnable or ex.language not in ("sql", "python", "r"):
        return
    if ex.language == "r" and not state.rscript():
        st.caption(t("R is not installed - this example cannot be run here."))
        with st.expander(t("How to enable R")):
            st.markdown(t(R_INSTALL_HELP))
        return
    edit_key = f"wex_code_{key}"
    st.session_state.setdefault(edit_key, ex.code)
    with st.expander(t("Edit and run this example"), expanded=False):
        st.text_area(t("Example code (edit freely - experimenting is encouraged)"), key=edit_key, height=260)
        c1, c2 = st.columns([1, 4])
        if c1.button(t("Run"), key=f"wex_run_{key}", icon=":material/play_arrow:", type="primary"):
            code = st.session_state[edit_key]
            with st.spinner(t("Running...")):
                if ex.language == "sql":
                    st.session_state[f"wex_out_{key}"] = ("sql", run_sql(code, state.run_settings(), ex.search_path))
                elif ex.language == "python":
                    st.session_state[f"wex_out_{key}"] = ("py", run_python(code, state.run_settings(), ex.preload))
                else:
                    st.session_state[f"wex_out_{key}"] = ("py", run_r(code, state.rscript(), state.run_settings(), ex.preload))
        if c2.button(t("Restore original"), key=f"wex_reset_{key}"):
            st.session_state.pop(edit_key, None)
            st.session_state.pop(f"wex_out_{key}", None)
            st.rerun()
        out = st.session_state.get(f"wex_out_{key}")
        if out:
            (show_sql_run if out[0] == "sql" else show_python_run)(out[1], f"wex_{key}")


def render_lesson(lesson: Lesson) -> None:
    store = state.store()
    store.start_lesson(lesson.id)
    status = store.lesson_status().get(lesson.id, {})
    st.markdown(f"## {lesson.title}")
    comps = ", ".join(COMP[c].name for c in lesson.competencies if c in COMP)
    st.markdown(f"{level_badge(lesson.level)} :gray-background[{' · '.join(lesson.tools)}] :gray-background[~{lesson.minutes} min]"
                + (f" :green-background[{t('completed')}]" if status.get("status") == "completed" else ""))
    st.caption(t("Competencies: {comps}", comps=comps))

    learn, check, practice, wrap = st.tabs([t("1-4 · Learn"), t("5 · Knowledge check"), t("6-8 · Practice & feedback"), t("9-10 · Summary & next steps")])
    with learn:
        st.markdown(t("### 1. Learning objectives"))
        st.markdown("\n".join(f"- {o}" for o in lesson.objectives))
        st.markdown(t("### 2. Concept"))
        st.markdown(lesson.concept)
        st.markdown(t("### 3. Business context"))
        st.info(lesson.business_context.strip(), icon=":material/business_center:")
        st.markdown(t("### 4. Worked solution"))
        for i, ex in enumerate([lesson.worked_example, *lesson.extra_examples]):
            if i:
                st.markdown(t("**Another example**"))
            st.code(ex.code, language=LANG.get(ex.language, "text"))
            st.markdown(ex.explanation)
            _run_example(ex, f"{lesson.id}_{i}")
        if lesson.common_mistakes:
            with st.expander(t("Common mistakes to avoid")):
                st.markdown("\n".join(f"- {m}" for m in lesson.common_mistakes))
    with check:
        st.markdown(t("### 5. Interactive knowledge check"))
        st.caption(t("Immediate feedback with an explanation for every option. Results count towards your knowledge score."))
        score = knowledge_check(lesson.knowledge_check, key=lesson.id)
        if score is not None:
            st.session_state[f"lesson_score_{lesson.id}"] = score
    with practice:
        st.markdown(t("### 6. Guided practical exercise"))
        if lesson.guided_exercise:
            st.caption(t("Guided: hints are available and the solution unlocks after your first attempt."))
            with st.container(border=True):
                render_exercise(EXERCISES_BY_ID[lesson.guided_exercise], prefix=f"les_{lesson.id}_g", compact=True)
        elif lesson.tool_workshop:
            st.caption(t("This lesson's guided practice is a tool workshop."))
        else:
            st.caption(t("No coded exercise for this lesson."))
        st.markdown(t("### 7. Independent challenge"))
        if lesson.challenge:
            st.caption(t("Independent: try without hints first - they are still there if you need them."))
            with st.container(border=True):
                render_exercise(EXERCISES_BY_ID[lesson.challenge], prefix=f"les_{lesson.id}_c", compact=True)
        if lesson.tool_workshop:
            with st.container(border=True):
                st.markdown(t("**Tool workshop: {name}**", name=t(WORKSHOPS[lesson.tool_workshop][0])))
                render_workshop(lesson.tool_workshop, key=f"les_{lesson.id}")
        if not lesson.challenge and not lesson.tool_workshop:
            st.markdown(t("Apply the technique to a different table or question of your choice in the **Practice & Coding Lab**, "
                          "or pick a related exercise from the *All module exercises* tab."))
        st.markdown(t("### 8. Feedback and explanation"))
        st.markdown(t("Each submission above returns check-by-check feedback, a score and a suggested next step. "
                      "Your attempt history and best score are stored; compare your code with the reference solution after attempting."))
    with wrap:
        st.markdown(t("### 9. Summary and key takeaways"))
        st.success("\n".join(f"- {s}" for s in lesson.summary))
        st.markdown(t("### 10. Suggested revision and next lesson"))
        if lesson.revision:
            st.markdown(t("**If this felt hard:** {text}", text=lesson.revision))
        kc = st.session_state.get(f"lesson_score_{lesson.id}", status.get("check_score"))
        c1, c2 = st.columns(2)
        label = t("Mark lesson as completed") if status.get("status") != "completed" else t("Completed ✔ (update score)")
        if c1.button(label, key=f"complete_{lesson.id}", type="primary", icon=":material/done_all:", disabled=kc is None and bool(lesson.knowledge_check)):
            store.complete_lesson(lesson.id, kc)
            st.toast(t("Lesson completed - nice work!"))
            st.rerun()
        if kc is None and lesson.knowledge_check:
            c1.caption(t("Complete the knowledge check (tab 5) to unlock completion."))
        if lesson.next_lesson:
            nxt = get_lesson(lesson.next_lesson)
            if nxt.module == lesson.module:
                # Same page: change the selectbox state in a callback (before widgets are rebuilt).
                c2.button(t("Next: {title}", title=nxt.title), key=f"next_{lesson.id}", icon=":material/arrow_forward:",
                          on_click=lambda: st.session_state.__setitem__(f"lesson_sel_{lesson.module}", nxt.id))
            elif c2.button(t("Next module: {title}", title=nxt.title), key=f"next_{lesson.id}", icon=":material/arrow_forward:"):
                state.open_lesson(nxt.id)
