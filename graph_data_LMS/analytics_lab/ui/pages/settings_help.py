"""Settings, capability check, reference library (glossary & cheat sheets), help and data management."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analytics_lab.capabilities import R_INSTALL_HELP, check_packages, python_info
from analytics_lab.config import get_paths
from analytics_lab.curriculum.reference import CHEATSHEETS, GLOSSARY, search_reference
from analytics_lab.data.generate import build_all
from analytics_lab.execution.sandbox import docker_available
from analytics_lab.i18n import t
from analytics_lab.ui import state

TRUST_MODEL = """
**Execution safety and trust model**

* The lab is designed for **one local user on their own computer**. The person writing code is the machine's owner.
* Learner code (Python, SQL, R) **never runs inside the Streamlit server process**. Each run starts a fresh child process with a
  wall-clock timeout (configurable), a temporary working directory that is deleted afterwards, and a minimal environment
  (API keys, tokens and other environment variables are not passed through). Python runs in isolated mode; on Linux/macOS memory and CPU limits are applied.
* SQL runs against **read-only** DuckDB files with external file/network access disabled and locked.
* This is **not a security sandbox**. A determined user can still read or modify files their account can access from Python or R.
  Do not run code from untrusted sources. For stronger isolation, enable the optional **Docker backend** (no network, read-only data mount,
  memory/CPU/process limits) after building the image described in the README.
* Hidden test code and reference solutions are never displayed in the interface before an attempt; because everything runs locally, they are not cryptographically secret.
* No cloud services, accounts or paid APIs are used. Excel, Power BI, Tableau and Looker Studio are **not** executed by the lab; their workshops provide data, tasks, expected results and simulations.
"""

HELP = """
### How to use the lab
1. **Dashboard** shows your completion, competencies and personalised recommendations (with the reason for each).
2. **Learning Path** lists all lessons by level and lets you search lessons, exercises and capstones.
3. **Module pages** contain the lessons. Each lesson: objectives -> concept -> business context -> worked solution (editable and runnable) -> knowledge check -> guided exercise -> independent challenge -> feedback -> summary -> next steps.
4. **Practice & Coding Lab**: SQL workbench, Python and R labs, all coding challenges, the dataset explorer, your own file imports and tool workshops.
5. **Assessment Center**: build quizzes (immediate / end / exam feedback, optional timer, randomised answers, retry with a new set), business cases with rubrics, the final competency assessment and attempt review.
6. **Capstone Projects**: five integrated projects with milestones and automated checks.
7. **My Progress**: competency profile, history, repeated mistakes and export.

### Tips
* Each code run starts fresh: define everything you need in the same editor.
* In Python, `load_table("schema.table")` and `sql("SELECT ...")` return DataFrames; assign a DataFrame to `result` to display it; figures are captured automatically.
* Hints are progressive. The reference solution unlocks after your first submission (or explicit confirmation); passing after viewing it counts as *assisted*.

### Troubleshooting
* *Code times out* - look for loops over rows or accidental cross joins; increase the timeout in Settings if the task is legitimately heavy.
* *R exercises are disabled* - install R or set the Rscript path (System check tab).
* *Excel checker finds no values* - open the workbook in Excel/LibreOffice and save it, so calculated values are stored.
* *Something looks broken* - Data management -> Regenerate datasets; progress is unaffected.
"""

FEEDBACK_MODES = {"immediate": "Immediate", "end": "At the end"}


def render() -> None:
    st.title(t("Settings & Help"))
    t_set, t_sys, t_ref, t_help, t_data = st.tabs([t("Settings"), t("System check"), t("Reference library"), t("Help"), t("Data management")])
    store = state.store()
    with t_set:
        s = store.get_settings()
        with st.form("settings_form"):
            name = st.text_input(t("Your name (shown on the dashboard)"), s.get("learner_name", ""))
            thr = st.slider(t("Mastery threshold (%)"), 50, 100, int(float(s.get("mastery_threshold", 80))), 5,
                            help=t("A competency counts as mastered at or above this score (plus practical evidence where required)."))
            timeout = st.slider(t("Code execution timeout (seconds)"), 5, 120, int(float(s.get("execution_timeout", 20))), 5)
            backend = st.radio(t("Execution backend"), ["local", "docker"], index=0 if s.get("execution_backend", "local") == "local" else 1, horizontal=True,
                               help=t("'local' = separate subprocess (default). 'docker' = container with no network; requires Docker and the runner image."))
            image = st.text_input(t("Docker image"), s.get("docker_image", "analytics-lab-runner:latest"))
            fb = st.radio(t("Default quiz feedback"), ["immediate", "end"], index=0 if s.get("quiz_feedback", "immediate") == "immediate" else 1, horizontal=True,
                          format_func=lambda v: t(FEEDBACK_MODES[v]))
            rpath = st.text_input(t("Path to Rscript (optional; auto-detected if empty)"), s.get("r_executable", ""))
            if st.form_submit_button(t("Save settings"), type="primary"):
                if backend == "docker" and not docker_available():
                    st.error(t("Docker is not available on this computer, so the backend stays 'local'. See README -> Optional Docker isolation."))
                    backend = "local"
                for k, v in {"learner_name": name, "mastery_threshold": thr, "execution_timeout": timeout, "execution_backend": backend,
                             "docker_image": image, "quiz_feedback": fb, "r_executable": rpath}.items():
                    store.set_setting(k, v)
                st.cache_data.clear()
                st.success(t("Settings saved."))
        st.caption(t("Language and dark theme: use the switches at the top of the sidebar. Both are remembered between sessions."))
    with t_sys:
        st.markdown(f"**{python_info()}**")
        pk = pd.DataFrame([p.__dict__ for p in check_packages()])
        pk["status"] = pk.apply(lambda r: t("✅ installed") if r["installed"] else (t("❌ missing (required)") if r["required"] else t("– not installed (optional)")), axis=1)
        st.dataframe(pk[["dist", "purpose", "version", "status"]].rename(columns=t), hide_index=True, width="stretch")
        if not pk[pk["required"] & ~pk["installed"]].empty:
            st.error(t("Some required packages are missing. Run `pip install -r requirements.txt` in your virtual environment."))
        r = state.r_status(store.get_setting("r_executable"))
        st.markdown(t("**R (optional)**"))
        if r.available:
            st.success(t("{version} at `{path}`. Packages: ", version=r.version, path=r.path) + ", ".join(f"{k} {'✅' if v else '–'}" for k, v in r.packages.items()))
        else:
            st.warning(t("R not found. All other modules work normally."))
            st.markdown(t(R_INSTALL_HELP))
        st.markdown(t("**Docker (optional)**"))
        st.markdown(t("✅ Docker is available.") if docker_available() else t("– Docker not found (only needed for the optional isolated backend)."))
        if st.button(t("Re-check capabilities"), key="recheck"):
            st.cache_data.clear()
            st.rerun()
        p = get_paths()
        st.markdown(t("**Data locations**  \nWarehouse: `{w}`  \nProgress DB: `{p}`  \nUploads: `{u}`", w=p.warehouse_db, p=p.progress_db, u=p.uploads_db))
    with t_ref:
        q = st.text_input(t("Search the glossary and cheat sheets"), placeholder=t("e.g. leakage, XLOOKUP, window, shadow price"), key="ref_q")
        if q:
            hits = search_reference(q)
            st.caption(t("{n} result(s)", n=len(hits)))
            for kind, title, text in hits:
                with st.expander(f"{t(kind)}: {title}", expanded=kind == "Glossary"):
                    st.markdown(text)
        g, c = st.tabs([t("Glossary"), t("Cheat sheets")])
        with g:
            for term in sorted(GLOSSARY, key=str.lower):
                st.markdown(f"**{term}** - {GLOSSARY[term]}")
        with c:
            sheet = st.radio(t("Tool"), list(CHEATSHEETS), horizontal=True, key="ref_sheet")
            st.markdown(CHEATSHEETS[sheet])
    with t_help:
        st.markdown(t(HELP))
        st.markdown(t(TRUST_MODEL))
    with t_data:
        st.markdown(t("**Datasets** are generated locally from seeded random generators, so they are identical on every machine."))
        if st.button(t("Regenerate datasets"), key="regen", icon=":material/autorenew:"):
            with st.spinner(t("Generating...")):
                st.cache_data.clear()
                build_all(force=True)
            st.success(t("Datasets regenerated."))
        st.divider()
        st.markdown(t("**Reset progress** - permanently deletes lessons, attempts, quiz results, case submissions and milestones. Export first if you want a backup (My Progress -> Export)."))
        keep = st.checkbox(t("Keep my settings"), value=True, key="reset_keep")
        confirm = st.text_input(t("Type RESET to confirm"), key="reset_confirm")
        if st.button(t("Reset all progress"), type="primary", disabled=confirm != "RESET", key="reset_btn", icon=":material/delete_forever:"):
            store.reset(keep_settings=keep)
            for k in list(st.session_state.keys()):
                if not k.startswith("_"):
                    del st.session_state[k]
            st.success(t("Progress reset."))
