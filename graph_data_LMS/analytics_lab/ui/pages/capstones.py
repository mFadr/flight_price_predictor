"""Capstone projects: brief, data, milestones with automated checks, rubrics and exemplars."""

from __future__ import annotations

import io
import json
import zipfile

import streamlit as st

from analytics_lab.assessment.bank import EXERCISES_BY_ID
from analytics_lab.assessment.capstones import CAPSTONES, CAPSTONES_BY_ID
from analytics_lab.data.catalog import dataset_markdown
from analytics_lab.data.loader import load_table
from analytics_lab.i18n import get_lang, t
from analytics_lab.models import Capstone, Milestone, MODULES
from analytics_lab.ui import state
from analytics_lab.ui.components.exercise import render_exercise


@st.cache_data(show_spinner=False)
def _data_zip(schemas: tuple[str, ...], lang: str = "en") -> bytes:
    from analytics_lab.data.catalog import DATASETS

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for s in schemas:
            for tbl in DATASETS[s].tables:
                z.writestr(f"{s}/{tbl.name}.csv", load_table(s, tbl.name).to_csv(index=False))
            z.writestr(f"{s}/DATA_DICTIONARY.md", dataset_markdown(s))
    return buf.getvalue()


def _brief_md(cap: Capstone) -> str:
    out = [t("# Capstone: {title}", title=cap.title), "", cap.brief.strip(), "", t("## Requirements")] + [f"- {r}" for r in cap.requirements]
    out += ["", t("## Milestones")] + [f"{i}. **{m.title}** - {m.description}" for i, m in enumerate(cap.milestones, 1)]
    out += ["", t("## Evaluation criteria")] + [f"- {e}" for e in cap.evaluation]
    out += ["", t("Datasets: {ds} (see data dictionaries in the data pack).", ds=", ".join(cap.datasets))]
    return "\n".join(out)


def render() -> None:
    store = state.store()
    st.title(t("Capstone Projects"))
    st.caption(t("Integrative projects that provide the practical evidence required for mastery. Each has a brief, data, milestones, automated checks where feasible, rubrics and an example of a strong submission."))
    ms = store.milestones()
    done_lessons = store.completed_lessons()

    ids = [c.id for c in CAPSTONES]
    if st.session_state.get("capstone_sel") not in ids:
        st.session_state["capstone_sel"] = ids[0]

    def fmt(cid: str) -> str:
        cap = CAPSTONES_BY_ID[cid]
        n = int(((ms["capstone_id"] == cid) & (ms["status"] == "completed")).sum()) if not ms.empty else 0
        return t("{title}  ({n}/{total} milestones)", title=cap.title, n=n, total=len(cap.milestones))

    st.selectbox(t("Capstone"), ids, key="capstone_sel", format_func=fmt)
    cap = CAPSTONES_BY_ID[st.session_state["capstone_sel"]]
    sub = ms[ms["capstone_id"] == cap.id] if not ms.empty else ms
    status = {r["milestone_id"]: r for _, r in sub.iterrows()} if len(sub) else {}
    n_done = sum(1 for m in cap.milestones if status.get(m.id, {}).get("status") == "completed")

    st.markdown(f"## {cap.title}")
    st.markdown(" ".join(f":gray-background[{MODULES[m]}]" for m in cap.modules))
    st.progress(n_done / len(cap.milestones), text=t("{n}/{total} milestones completed", n=n_done, total=len(cap.milestones)))
    missing = [p for p in cap.prerequisites if p not in done_lessons]
    if missing:
        st.info(t("Recommended lessons before starting: {lessons}. You can start anyway.", lessons=", ".join(missing)))

    t_brief, t_ms, t_eval = st.tabs([t("Brief & data"), t("Milestones"), t("Evaluation & strong example")])
    with t_brief:
        st.markdown(cap.brief)
        st.markdown(t("**Requirements**") + "\n" + "\n".join(f"- {r}" for r in cap.requirements))
        c1, c2 = st.columns(2)
        c1.download_button(t("Download project brief (.md)"), _brief_md(cap), f"capstone_{cap.id}_brief.md", key=f"cap_brief_{cap.id}", icon=":material/description:")
        with st.spinner(t("Packaging data...")):
            pack = _data_zip(tuple(cap.datasets), get_lang())
        c2.download_button(t("Download data pack (.zip)"), pack, f"capstone_{cap.id}_data.zip", "application/zip", key=f"cap_zip_{cap.id}", icon=":material/download:")
    with t_ms:
        for i, m in enumerate(cap.milestones, 1):
            row = status.get(m.id)
            badge = "✅" if row is not None and row["status"] == "completed" else ("🟡" if row is not None else "⬜")
            with st.expander(t("{badge} Milestone {i}: {title}", badge=badge, i=i, title=m.title), expanded=row is None or row["status"] != "completed"):
                st.markdown(m.description)
                _milestone(cap, m, row)
    with t_eval:
        st.markdown(t("**Evaluation criteria**") + "\n" + "\n".join(f"- {e}" for e in cap.evaluation))
        st.markdown(t("**Example of a strong final submission**"))
        if n_done == 0 and not st.checkbox(t("Show the example now (it is more useful after you attempt the milestones)"), key=f"cap_ex_{cap.id}"):
            st.caption(t("Complete at least one milestone to unlock, or tick the box above."))
        else:
            st.success(cap.strong_example)


def _milestone(cap: Capstone, m: Milestone, row) -> None:
    store = state.store()
    key = f"cap_{cap.id}_{m.id}"
    if m.kind == "exercise":
        ex = EXERCISES_BY_ID[m.exercise_id]
        summary = store.exercise_summary()
        already = (not summary.empty) and bool(summary[(summary["exercise_id"] == ex.id) & (summary["passed"] == 1)].shape[0])
        if already and (row is None or row["status"] != "completed"):
            best = float(summary[summary["exercise_id"] == ex.id]["best_score"].iloc[0])
            store.set_milestone(cap.id, m.id, "completed", best, "exercise passed")
            st.success(t("You already passed this exercise - milestone completed."))

        def on_pass(g):
            store.set_milestone(cap.id, m.id, "completed", g.score, "exercise passed")
            st.toast(t("Milestone completed!"))

        render_exercise(ex, prefix=key, on_pass=on_pass, compact=True)
    elif m.kind == "checklist":
        prev = json.loads(row["evidence"]) if row is not None and row["evidence"] and str(row["evidence"]).startswith("[") else []
        # Evidence stores ticked item positions (older saves stored the item texts), so ticks survive a language switch.
        checks = [st.checkbox(c, value=j in prev or c in prev, key=f"{key}_c{j}") for j, c in enumerate(m.checklist)]
        if st.button(t("Save checklist"), key=f"{key}_save"):
            ticked = [j for j, v in enumerate(checks) if v]
            score = 100 * len(ticked) / len(m.checklist)
            store.set_milestone(cap.id, m.id, "completed" if score == 100 else "in_progress", score, json.dumps(ticked))
            st.toast(t("Saved ({s:.0f}%). Checklist items are self-assessed.", s=score))
            st.rerun()
    else:  # text deliverable + rubric self-assessment
        prev_text = ""
        if row is not None and row["evidence"]:
            try:
                prev_text = json.loads(row["evidence"]).get("text", "")
            except (ValueError, AttributeError):
                prev_text = str(row["evidence"])
        text = st.text_area(t("Your deliverable"), value=prev_text, height=220, key=f"{key}_text")
        st.markdown(t("**Rubric self-assessment** (transparent, self-applied - not automatically graded)"))
        levels = {}
        for crit in m.rubric:
            levels[crit.name] = st.select_slider(f"{crit.name} - {crit.description}", options=list(range(4)), value=0,
                                                 format_func=lambda v, c=crit: c.levels[v], key=f"{key}_{crit.name}")
        if st.button(t("Save deliverable"), key=f"{key}_save", type="primary", disabled=len(text.strip()) < 40):
            score = round(100 * sum(levels.values()) / (3 * len(m.rubric)), 1) if m.rubric else None
            store.set_milestone(cap.id, m.id, "completed", score, json.dumps({"text": text, "rubric": levels}))
            st.toast(t("Saved (self-assessed {s:.0f}%).", s=score))
            st.rerun()
        if len(text.strip()) < 40:
            st.caption(t("Write at least a few sentences to save."))
