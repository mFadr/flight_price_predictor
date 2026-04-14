"""Dashboard: progress overview, competencies and adaptive recommendations."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics_lab.competency import completion_summary, compute_competencies, module_scores, outstanding, recommend
from analytics_lab.i18n import get_lang, t, tr
from analytics_lab.models import MODULE_QUESTIONS, MODULES
from analytics_lab.ui import state

KIND_ICON = {"lesson": ":material/menu_book:", "exercise": ":material/code:", "quiz": ":material/quiz:", "capstone": ":material/flag:"}


def _open(rec) -> None:
    if rec.kind == "lesson":
        state.open_lesson(rec.target)
    elif rec.kind == "exercise":
        state.open_exercise(rec.target)
    elif rec.kind == "capstone":
        state.open_capstone(rec.target)
    elif rec.kind == "quiz":
        state.go("assessment", assess_tab="Quiz", quiz_preset="review")


def render() -> None:
    store = state.store()
    thr = state.threshold()
    name = store.get_setting("learner_name").strip()
    st.title(t("Welcome back, {name}", name=name) if name else t("Welcome back"))
    st.caption(t("Learn by doing: define the question, inspect the data, choose a method, validate, interpret, communicate."))

    s = completion_summary(store)
    c = st.columns(6)
    c[0].metric(t("Overall completion"), f"{s['completion_pct']:.0f}%", help=t("Completed items / all items (lessons + coding exercises + capstone milestones)."), border=True)
    c[1].metric(t("Lessons"), f"{s['lessons_done']}/{s['lessons_total']}", border=True)
    c[2].metric(t("Quiz accuracy"), f"{s['quiz_accuracy']:.0f}%" if s["quiz_accuracy"] is not None else "-", help=t("{n} questions answered", n=s["questions_answered"]), border=True)
    c[3].metric(t("Exercise pass rate"), f"{s['exercise_pass_rate']:.0f}%" if s["exercise_pass_rate"] is not None else "-",
                help=t("Share of {n} submissions that passed all checks", n=s["submissions"]), border=True)
    c[4].metric(t("Exercises passed"), f"{s['exercises_passed']}/{s['exercises_total']}", border=True)
    c[5].metric(t("Learning streak"), t("{n} day", n=s["streak"]) if s["streak"] == 1 else t("{n} days", n=s["streak"]), help=t("Consecutive days with recorded activity"), border=True)

    left, right = st.columns([3, 2])
    with left:
        st.subheader(t("Recommended for you"))
        recs = recommend(store, thr)
        for i, rec in enumerate(recs):
            with st.container(border=True):
                a, b = st.columns([5, 1], vertical_alignment="center")
                a.markdown(f"**{rec.title}**  \n{rec.reason}")
                if b.button(t("Open"), key=f"rec_{i}", icon=KIND_ICON.get(rec.kind), width="stretch",
                            help=t("You can always choose any lesson yourself from the navigation menu.")):
                    _open(rec)
        st.caption(t("Recommendations adapt to your quiz accuracy, repeated mistakes, exercise attempts and completed prerequisites. You can ignore them and pick any lesson."))

    with right:
        st.subheader(t("Competency by module"))
        scores = compute_competencies(store, thr)
        ms = module_scores(scores)
        df = pd.DataFrame({"module": [MODULES[m] for m in ms], "score": [v if v is not None else 0 for v in ms.values()],
                           "has_evidence": [v is not None for v in ms.values()]})
        fig = px.bar(df, x="score", y="module", orientation="h", range_x=[0, 100], text=df["score"].map(lambda v: f"{v:.0f}" if v else t("no data")), height=260)
        fig.add_vline(x=thr, line_dash="dash", line_color="#64748b", annotation_text=t("mastery {thr:.0f}", thr=thr), annotation_position="top")
        fig.update_traces(marker_color="#2563eb")
        fig.update_layout(margin=dict(l=0, r=10, t=10, b=0), xaxis_title=t("Competency score"), yaxis_title=None)
        st.plotly_chart(fig, key="dash_modules")
        evidenced = [x for x in scores if x.score is not None]
        if evidenced:
            best = max(evidenced, key=lambda x: x.score)
            worst = min(evidenced, key=lambda x: x.score)
            if best.id == worst.id:
                st.markdown(t("**Evidence so far:** {name} ({score:.0f}). Strongest and weakest appear once you have evidence for two or more competencies.",
                              name=best.name, score=best.score))
            else:
                st.markdown(t("**Strongest:** {best} ({bs:.0f}) · **Weakest:** {worst} ({ws:.0f})", best=best.name, bs=best.score, worst=worst.name, ws=worst.score))
        else:
            st.caption(t("Complete a knowledge check or exercise to see your strongest and weakest competencies."))

    a, b = st.columns(2)
    with a:
        st.subheader(t("Outstanding work"))
        items = outstanding(store)
        if items:
            st.markdown("\n".join(f"- {i}" for i in items[:8]))
        else:
            st.caption(t("Nothing outstanding. Start a lesson or a capstone to build momentum."))
    with b:
        st.subheader(t("Recent activity"))
        act = store.recent_activity(8)
        if act.empty:
            st.caption(t("No activity yet."))
        else:
            act["ts"] = pd.to_datetime(act["ts"]).dt.strftime("%d.%m. %H:%M" if get_lang() == "cs" else "%d %b %H:%M")
            act["kind"] = act["kind"].map(tr)
            st.dataframe(act.rename(columns={"ts": t("When"), "kind": t("Activity"), "ref": t("Item"), "detail": t("Detail")}), hide_index=True, width="stretch")

    with st.expander(t("The five modules")):
        for m, title in MODULES.items():
            st.markdown(f"**{title}** - *{MODULE_QUESTIONS[m]}*")
