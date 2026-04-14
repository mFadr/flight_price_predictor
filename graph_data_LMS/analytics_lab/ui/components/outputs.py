"""Rendering helpers for code output, data previews and evidence blocks."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analytics_lab.data.catalog import table_doc
from analytics_lab.execution.runners import PythonRun, RRun, SQLRun
from analytics_lab.i18n import t


@st.cache_data(show_spinner=False, ttl=3600)
def cached_columns(schema: str, table: str) -> pd.DataFrame:
    from analytics_lab.data.loader import table_columns

    return table_columns(schema, table)


def schema_panel(tables: list[str]) -> None:
    """Show columns, types and descriptions for 'schema.table' names."""
    for full in tables:
        schema, _, table = full.partition(".")
        doc = table_doc(schema, table)
        cols = cached_columns(schema, table)
        st.markdown(f"**`{full}`** - {doc.description if doc else ''}  \n*{t('Grain')}:* {doc.grain if doc else 'n/a'}")
        if doc:
            cols = cols.assign(description=cols["column_name"].map(doc.columns).fillna(""))
        st.dataframe(cols, hide_index=True, width="stretch")


def show_frame(df: pd.DataFrame | None, caption: str = "", height: int | None = None, key: str | None = None) -> None:
    if df is None:
        return
    if df.empty:
        st.info(t("The query returned no rows."))
        return
    st.dataframe(df, hide_index=True, width="stretch", height=height or "auto")
    c1, c2 = st.columns([3, 1])
    c1.caption(caption or t("{r:,} rows x {c} columns", r=len(df), c=df.shape[1]))
    c2.download_button(t("Download CSV"), df.to_csv(index=False).encode(), "result.csv", "text/csv", key=key, width="stretch")


def show_sql_run(run: SQLRun, key: str) -> None:
    if run.timed_out or not run.ok:
        st.error(run.error or t("The query failed."))
        if run.hint:
            st.info(t("**Hint:** {hint}", hint=t(run.hint)))
        return
    extra = t(" (truncated for display)") if run.truncated else ""
    show_frame(run.frame, t("{r:,} rows x {c} columns", r=len(run.frame), c=run.frame.shape[1]) + f"{extra} - {run.duration * 1000:.0f} ms", key=f"dl_{key}")


def show_python_run(run: PythonRun | RRun, key: str) -> None:
    if run.stdout:
        st.markdown(t("**Output**"))
        st.code(run.stdout, language="text")
    if run.error:
        st.error(t("Error"))
        st.code(run.error, language="text")
    if getattr(run, "stderr", "") and not run.error:
        with st.expander(t("Warnings / messages")):
            st.code(run.stderr[-5000:], language="text")
    for i, png in enumerate(run.figures):
        st.image(png, caption=t("Figure {n}", n=i + 1), width="stretch")
    res = getattr(run, "result", None)
    if isinstance(res, pd.DataFrame):
        shape = getattr(run, "result_shape", None)
        st.markdown("**`result`**" + (t(" - shape {s}", s=tuple(shape)) if shape else ""))
        show_frame(res, key=f"dl_{key}")
    elif getattr(run, "result_repr", None):
        st.markdown("**`result`**")
        st.code(run.result_repr, language="text")
    variables = getattr(run, "variables", None)
    if variables:
        with st.expander(t("Variables defined ({n})", n=len(variables))):
            st.dataframe(pd.DataFrame(variables), hide_index=True, width="stretch")
    if not (run.stdout or run.error or run.figures or res is not None or getattr(run, "result_repr", None)):
        st.caption(t("Code ran without output. Use print(...) or assign a DataFrame to `result` to see it here."))
    st.caption(t("Ran in a separate process in {d:.2f}s.", d=run.duration))


def evidence_blocks(blocks: list[tuple[str, object]]) -> None:
    for kind, content in blocks:
        if kind == "md":
            st.markdown(content)
        elif kind == "table":
            st.dataframe(content, hide_index=True, width="stretch")
        elif kind == "img":
            st.image(content, width="stretch")


def level_badge(level: str) -> str:
    colors = {"Beginner": "green", "Intermediate": "blue", "Advanced": "orange", "Professional": "violet"}
    return f":{colors.get(level, 'gray')}-background[{t(level)}]"
