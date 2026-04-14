"""Data Analytics Learning & Testing Lab - Streamlit entry point.

Run:  streamlit run app.py   (then open http://localhost:8501)
"""

from __future__ import annotations

import importlib
import sys

import streamlit as st
from streamlit import runtime

# Launched as `python app.py`? Re-launch through Streamlit so session state and the web server work.
if __name__ == "__main__" and not runtime.exists():
    from streamlit.web import cli as stcli

    sys.argv = ["streamlit", "run", __file__, *sys.argv[1:]]
    sys.exit(stcli.main())

st.set_page_config(page_title="Data Analytics Lab", page_icon=":material/insights:", layout="wide", initial_sidebar_state="expanded")

# --- Fail gracefully if a required dependency is missing -----------------------------------
_missing = []
for _mod in ("pandas", "numpy", "duckdb", "scipy", "statsmodels", "sklearn", "matplotlib", "plotly", "openpyxl"):
    try:
        importlib.import_module(_mod)
    except ImportError:
        _missing.append(_mod)
if _missing:
    st.error(f"Missing required Python packages: {', '.join(_missing)}.\n\nInstall them with `pip install -r requirements.txt` and restart the app.")
    st.stop()

from analytics_lab.data.generate import build_all, datasets_ready  # noqa: E402
from analytics_lab.i18n import LANGUAGES, apply_language, t  # noqa: E402
from analytics_lab.ui import state  # noqa: E402
from analytics_lab.ui.pages import (  # noqa: E402
    assessment_center,
    capstones,
    dashboard,
    learning_path,
    practice_lab,
    progress,
    settings_help,
)
from analytics_lab.ui.pages.module import render_module  # noqa: E402

# --- Language and theme (saved in Settings, switchable from the sidebar) --------------------
_saved = state.settings()
apply_language(_saved.get("language", "en"))


def _apply_theme(mode: str) -> None:
    """Switch Streamlit's base theme at runtime; the browser picks it up on the next run."""
    base = "dark" if mode == "dark" else "light"
    if st._config.get_option("theme.base") != base:
        st._config.set_option("theme.base", base)
        st.rerun()


_apply_theme(_saved.get("theme", "light"))


def _save_language() -> None:
    state.store().set_setting("language", st.session_state["ui_language"])


def _save_theme() -> None:
    state.store().set_setting("theme", "dark" if st.session_state["ui_dark"] else "light")


st.markdown(
    """
<style>
textarea { font-family: "JetBrains Mono", "Cascadia Code", Consolas, "Courier New", monospace !important; font-size: 0.88rem !important; }
[data-testid="stMetricValue"] { font-size: 1.6rem; }
.block-container { padding-top: 2.2rem; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def _bootstrap() -> bool:
    build_all()
    return True


if not datasets_ready():
    with st.spinner(t("First start: generating the practice datasets (takes a few seconds)...")):
        _bootstrap()
else:
    _bootstrap()


def _module(mid: str):
    def page() -> None:
        render_module(mid)

    page.__name__ = f"module_{mid}"
    return page


pages = {
    "dashboard": st.Page(dashboard.render, title=t("Dashboard"), icon=":material/dashboard:", default=True),
    "path": st.Page(learning_path.render, title=t("Learning Path"), icon=":material/route:", url_path="learning-path"),
    "descriptive": st.Page(_module("descriptive"), title=t("Descriptive Analytics"), icon=":material/table_chart:", url_path="descriptive"),
    "diagnostic": st.Page(_module("diagnostic"), title=t("Diagnostic Analytics"), icon=":material/troubleshoot:", url_path="diagnostic"),
    "predictive": st.Page(_module("predictive"), title=t("Predictive Analytics"), icon=":material/trending_up:", url_path="predictive"),
    "prescriptive": st.Page(_module("prescriptive"), title=t("Prescriptive Analytics"), icon=":material/tune:", url_path="prescriptive"),
    "visualization": st.Page(_module("visualization"), title=t("Data Visualization"), icon=":material/bar_chart:", url_path="visualization"),
    "practice": st.Page(practice_lab.render, title=t("Practice & Coding Lab"), icon=":material/code:", url_path="practice"),
    "assessment": st.Page(assessment_center.render, title=t("Assessment Center"), icon=":material/quiz:", url_path="assessment"),
    "capstones": st.Page(capstones.render, title=t("Capstone Projects"), icon=":material/flag:", url_path="capstones"),
    "progress": st.Page(progress.render, title=t("My Progress"), icon=":material/monitoring:", url_path="progress"),
    "settings": st.Page(settings_help.render, title=t("Settings & Help"), icon=":material/settings:", url_path="settings"),
}
state.register_pages(pages)

nav = st.navigation(
    {
        t("Overview"): [pages["dashboard"], pages["path"]],
        t("Learning modules"): [pages[k] for k in ("descriptive", "diagnostic", "predictive", "prescriptive", "visualization")],
        t("Practice & assessment"): [pages["practice"], pages["assessment"], pages["capstones"]],
        t("You"): [pages["progress"], pages["settings"]],
    }
)

with st.sidebar:
    st.session_state.setdefault("ui_language", _saved.get("language", "en"))
    st.session_state.setdefault("ui_dark", _saved.get("theme", "light") == "dark")
    st.selectbox(":material/translate: " + t("Language"), list(LANGUAGES), format_func=LANGUAGES.get, key="ui_language", on_change=_save_language)
    st.toggle(":material/dark_mode: " + t("Dark theme"), key="ui_dark", on_change=_save_theme)
    try:
        from analytics_lab.competency import completion_summary

        s = completion_summary(state.store())
        st.progress(s["completion_pct"] / 100, text=t("Overall completion {pct:.0f}%", pct=s["completion_pct"]))
    except Exception as exc:  # never let the sidebar break navigation
        st.caption(t("Progress unavailable: {exc}", exc=exc))
    st.caption(t("Runs locally · no cloud services · your data stays on this computer."))

nav.run()
