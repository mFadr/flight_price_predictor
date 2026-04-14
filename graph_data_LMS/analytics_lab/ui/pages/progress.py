"""My Progress: competency profile, mastery, history, repeated mistakes and export."""

from __future__ import annotations

import io
import json
import zipfile

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics_lab import competency as comp_mod
from analytics_lab.assessment.bank import QUESTIONS_BY_ID
from analytics_lab.i18n import t
from analytics_lab.models import MODULES
from analytics_lab.ui import state

STATUS_COLOR = {"Mastered": "#16a34a", "Needs practical evidence": "#f59e0b", "Needs more evidence": "#f59e0b",
                "Developing": "#2563eb", "Needs work": "#dc2626", "Not started": "#94a3b8"}


def render() -> None:
    store = state.store()
    thr = state.threshold()
    st.title(t("My Progress"))
    scores = comp_mod.compute_competencies(store, thr)
    df = comp_mod.competency_frame(scores)
    s = comp_mod.completion_summary(store)
    c = st.columns(4)
    c[0].metric(t("Mastered competencies"), f"{(df['status'] == 'Mastered').sum()}/{len(df)}", border=True)
    c[1].metric(t("Overall completion"), f"{s['completion_pct']:.0f}%", border=True)
    c[2].metric(t("Questions answered"), s["questions_answered"], border=True)
    c[3].metric(t("Code submissions"), s["submissions"], border=True)

    t1, t2, t3, t4 = st.tabs([t("Competency profile"), t("History & improvement"), t("Repeated mistakes"), t("Export")])
    with t1:
        ms = comp_mod.module_scores(scores)
        radar = go.Figure(go.Scatterpolar(r=[v or 0 for v in ms.values()] + [list(ms.values())[0] or 0],
                                          theta=[MODULES[m] for m in ms] + [MODULES[list(ms)[0]]], fill="toself", line_color="#2563eb"))
        radar.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=360, margin=dict(l=40, r=40, t=30, b=30), showlegend=False)
        a, b = st.columns([2, 3])
        a.plotly_chart(radar, key="prog_radar")
        plot = df.copy()
        plot["score_plot"] = plot["score"].fillna(0)
        plot["status"] = plot["status"].map(t)
        fig = px.bar(plot.sort_values("score_plot"), x="score_plot", y="name", color="status", orientation="h",
                     color_discrete_map={t(k): v for k, v in STATUS_COLOR.items()}, range_x=[0, 100], height=640, labels={"score_plot": t("Score"), "name": ""})
        fig.add_vline(x=thr, line_dash="dash", line_color="#64748b")
        fig.update_layout(margin=dict(l=0, r=10, t=10, b=0), legend_title=None)
        b.plotly_chart(fig, key="prog_bars")
        show = df[["name", "module", "status", "score", "knowledge", "n_questions", "practical", "coverage", "n_exercises", "application", "n_applications", "requires_practical"]].copy()
        show["module"] = show["module"].map(MODULES)
        show["status"] = show["status"].map(t)
        show["coverage"] = (show["coverage"] * 100).round(0)
        for col in ("score", "knowledge", "practical", "application"):
            show[col] = pd.to_numeric(show[col], errors="coerce").round(0)
        st.dataframe(show.rename(columns={"name": "Competency", "n_questions": "# questions", "coverage": "exercise coverage %", "n_exercises": "# exercises",
                                          "n_applications": "# cases/projects", "requires_practical": "needs practical evidence"}).rename(columns=t), hide_index=True, width="stretch")
        with st.expander(t("How competency scores and mastery are calculated")):
            st.markdown(t(comp_mod.__doc__.split("\n", 2)[2]))
            st.markdown(t("Current mastery threshold: **{thr:.0f}%** (change it in Settings).", thr=thr))
    with t2:
        hist = store.quiz_history()
        ex = store.exercise_attempts()
        if hist.empty and ex.empty:
            st.info(t("No history yet - complete a knowledge check or submit an exercise."))
        if not hist.empty:
            hist["finished_at"] = pd.to_datetime(hist["finished_at"])
            fig = px.line(hist, x="finished_at", y="score", color="kind", markers=True, range_y=[0, 105], height=300,
                          labels={"finished_at": "", "score": t("Quiz score (%)"), "kind": t("kind")}, title=t("Quiz scores over time"))
            st.plotly_chart(fig, key="prog_quiz")
        if not ex.empty:
            ex["submitted_at"] = pd.to_datetime(ex["submitted_at"])
            ex["attempt_no"] = ex.groupby("exercise_id").cumcount() + 1
            first_last = ex.groupby("exercise_id").agg(first=("score", "first"), best=("score", "max"), attempts=("score", "size"))
            improved = first_last[first_last["attempts"] > 1]
            if len(improved):
                st.metric(t("Average improvement from first to best attempt"), t("{v:+.0f} points", v=(improved["best"] - improved["first"]).mean()),
                          help=t("Across exercises you attempted more than once"))
            fig = px.scatter(ex, x="submitted_at", y="score", color="module", symbol=ex["passed"].map({1: t("passed"), 0: t("not passed")}),
                             hover_data=["exercise_id", "attempt_no"], height=320, range_y=[-5, 105], title=t("Code submissions over time"))
            st.plotly_chart(fig, key="prog_ex")
            st.dataframe(first_last.reset_index().rename(columns=t), hide_index=True, width="stretch")
        lessons = store.lesson_status()
        if lessons:
            ld = pd.DataFrame(lessons.values())
            st.markdown(t("**Lessons**"))
            st.dataframe(ld.rename(columns=t), hide_index=True, width="stretch")
    with t3:
        resp = store.responses()
        if resp.empty:
            st.info(t("No answered questions yet."))
        else:
            by_topic = resp.groupby(["module", "topic"])["correct"].agg(answered="size", correct="sum").reset_index()
            by_topic["wrong"] = by_topic["answered"] - by_topic["correct"]
            by_topic["accuracy %"] = (100 * by_topic["correct"] / by_topic["answered"]).round(0)
            by_topic["module"] = by_topic["module"].map(MODULES)
            by_topic["topic"] = by_topic["topic"].map(t)
            st.markdown(t("**Topics with the most mistakes**"))
            st.dataframe(by_topic.sort_values(["wrong", "accuracy %"], ascending=[False, True]).rename(columns=t), hide_index=True, width="stretch")
            last = resp.sort_values("response_id").groupby("question_id").agg(times=("correct", "size"), wrong=("correct", lambda s: int((s == 0).sum())), last_correct=("correct", "last"))
            rep = last[last["wrong"] >= 2].reset_index()
            if len(rep):
                rep["question"] = rep["question_id"].map(lambda q: QUESTIONS_BY_ID[q].stem[:100] if q in QUESTIONS_BY_ID else q)
                st.markdown(t("**Questions missed more than once**"))
                st.dataframe(rep[["question", "times", "wrong", "last_correct"]].rename(columns=t), hide_index=True, width="stretch")
        ex = store.exercise_attempts()
        if not ex.empty:
            fails = []
            for _, r in ex[ex["passed"] == 0].iterrows():
                try:
                    fb = json.loads(r["feedback"] or "{}")
                except ValueError:
                    continue
                for item in fb.get("items", []):
                    if not item.get("passed"):
                        fails.append({t("exercise"): r["exercise_id"], t("check"): t(item.get("name") or "")})
            if fails:
                f = pd.DataFrame(fails).value_counts().reset_index(name=t("times failed"))
                st.markdown(t("**Most frequently failed automated checks**"))
                st.dataframe(f.head(15), hide_index=True, width="stretch")
    with t4:
        data = store.export_all()
        st.download_button(t("Download all progress (JSON)"), json.dumps(data, indent=2, default=str), "analytics_lab_progress.json", "application/json", icon=":material/download:")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, rows in data.items():
                z.writestr(f"{name}.csv", pd.DataFrame(rows).to_csv(index=False))
            z.writestr("competencies.csv", df.to_csv(index=False))
        st.download_button(t("Download all progress (CSV zip)"), buf.getvalue(), "analytics_lab_progress.zip", "application/zip", icon=":material/folder_zip:")
        st.caption(t("Reset options are under Settings & Help -> Data management."))
