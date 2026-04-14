"""Landing page with the learning path, search and filtering across content."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analytics_lab.assessment.bank import EXERCISES
from analytics_lab.assessment.capstones import CAPSTONES
from analytics_lab.curriculum import LESSONS
from analytics_lab.i18n import t
from analytics_lab.models import LEVELS, MODULES
from analytics_lab.ui import state

WORKFLOW = ["Define the business question", "Inspect & validate the data", "Select an appropriate method",
            "Validate the result", "Interpret the evidence", "Communicate the recommendation"]
KINDS = ["Lesson", "Exercise", "Capstone"]


def render() -> None:
    store = state.store()
    done = store.completed_lessons()
    st.title(t("Learning Path"))
    st.markdown(t("Every lesson follows the same rhythm - objectives, concept, business context, worked solution, knowledge check, "
                  "guided exercise, independent challenge, feedback, summary and next steps - and trains the analyst workflow:"))
    cols = st.columns(len(WORKFLOW))
    for i, (c, w) in enumerate(zip(cols, WORKFLOW), 1):
        c.markdown(f"<div style='text-align:center;padding:.5rem;border:1px solid rgba(128,128,128,.35);border-radius:.5rem;min-height:4.5rem'>"
                   f"<b>{i}</b><br><small>{t(w)}</small></div>", unsafe_allow_html=True)
    st.write("")

    tab_path, tab_search = st.tabs([t("Recommended path"), t("Search & filter")])
    with tab_path:
        st.caption(t("Levels run Beginner -> Professional. You may take lessons in any order; the path is a recommendation."))
        for level in LEVELS:
            lv = [lesson for lesson in LESSONS if lesson.level == level]
            if not lv:
                continue
            n_done = sum(lesson.id in done for lesson in lv)
            st.markdown(t("### {level} · {done}/{total} completed", level=t(level), done=n_done, total=len(lv)))
            grid = st.columns(3)
            for i, lesson in enumerate(sorted(lv, key=lambda x: x.order)):
                with grid[i % 3].container(border=True):
                    st.markdown(f"{'✅ ' if lesson.id in done else ''}**{lesson.title}**")
                    st.caption(f"{MODULES[lesson.module]} · {', '.join(lesson.tools)} · ~{lesson.minutes} min")
                    if st.button(t("Open lesson"), key=f"lp_{lesson.id}", width="stretch"):
                        state.open_lesson(lesson.id)
        st.markdown(t("### Professional capstones"))
        grid = st.columns(3)
        for i, cap in enumerate(CAPSTONES):
            with grid[i % 3].container(border=True):
                ready = all(p in done for p in cap.prerequisites)
                st.markdown(f"**{cap.title}**")
                st.caption(t("Prerequisites complete") if ready else t("Recommended first: {lessons}", lessons=", ".join(cap.prerequisites)))
                if st.button(t("Open capstone"), key=f"lp_cap_{cap.id}", width="stretch"):
                    state.open_capstone(cap.id)

    with tab_search:
        q = st.text_input(t("Search lessons, exercises and capstones"), placeholder=t("e.g. window functions, churn, threshold, Tableau"), key="lp_search")
        c1, c2, c3, c4 = st.columns(4)
        f_mod = c1.multiselect(t("Module"), list(MODULES), format_func=MODULES.get, key="lp_f_mod")
        f_lvl = c2.multiselect(t("Level"), LEVELS, format_func=t, key="lp_f_lvl")
        tools = sorted({tool for lesson in LESSONS for tool in lesson.tools} | {e.language.upper() for e in EXERCISES})
        f_tool = c3.multiselect(t("Tool / language"), tools, key="lp_f_tool")
        f_type = c4.multiselect(t("Type"), KINDS, format_func=t, key="lp_f_type")
        items = []
        for lesson in LESSONS:
            text = " ".join([lesson.title, lesson.concept, lesson.business_context, " ".join(lesson.objectives), " ".join(lesson.tools)]).lower()
            items.append(("Lesson", lesson.id, lesson.title, lesson.module, lesson.level, lesson.tools, text))
        for e in EXERCISES:
            text = " ".join([e.title, e.topic, e.business_question, " ".join(e.requirements)]).lower()
            items.append(("Exercise", e.id, e.title, e.module, e.difficulty, [e.language.upper()], text))
        for cap in CAPSTONES:
            items.append(("Capstone", cap.id, cap.title, cap.modules[0], "Professional", [], (cap.title + cap.brief).lower()))
        res = [it for it in items
               if (not q or all(w in it[6] for w in q.lower().split()))
               and (not f_mod or it[3] in f_mod) and (not f_lvl or it[4] in f_lvl)
               and (not f_tool or set(it[5]) & set(f_tool)) and (not f_type or it[0] in f_type)]
        st.caption(t("{n} result(s)", n=len(res)))
        for kind, iid, title, mod, lvl, tl, _ in res[:60]:
            a, b = st.columns([6, 1], vertical_alignment="center")
            a.markdown(f"**{title}**  \n:gray[{t(kind)} · {MODULES.get(mod, mod)} · {t(lvl)}{' · ' + ', '.join(tl) if tl else ''}]")
            if b.button(t("Open"), key=f"lps_{kind}_{iid}", width="stretch"):
                {"Lesson": state.open_lesson, "Exercise": state.open_exercise, "Capstone": state.open_capstone}[kind](iid)
