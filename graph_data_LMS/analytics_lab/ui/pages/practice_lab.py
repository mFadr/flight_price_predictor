"""Practice & Coding Lab: SQL workbench, Python/R labs, challenges, datasets, uploads, tool workshops."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics_lab.assessment.bank import EXERCISES, EXERCISES_BY_ID
from analytics_lab.capabilities import R_INSTALL_HELP
from analytics_lab.data import loader
from analytics_lab.data.catalog import DATASETS, dataset_markdown, table_doc
from analytics_lab.execution.runners import run_python, run_r, run_sql
from analytics_lab.i18n import t
from analytics_lab.models import LEVELS, MODULES
from analytics_lab.ui import state
from analytics_lab.ui.components.exercise import render_exercise
from analytics_lab.ui.components.outputs import cached_columns, show_python_run, show_sql_run
from analytics_lab.ui.components.workshops import WORKSHOPS, render_workshop

SECTIONS = ["SQL workbench", "Python lab", "R lab", "Coding challenges", "Dataset explorer", "Import data", "Tool workshops"]

PY_STARTER = """# Datasets: load_table("retail.orders") or sql("SELECT ...") return pandas DataFrames.
orders = load_table("retail.orders")
print(orders.shape)
result = orders.groupby("region").size().rename("orders").to_frame()   # DataFrames assigned to `result` are displayed

fig, ax = plt.subplots(figsize=(7, 3))
result["orders"].sort_values().plot.barh(ax=ax, color="#2563eb")
ax.set_xlabel("Orders"); ax.set_title("Orders by region")
"""
R_STARTER = """# load_table("schema.table") returns a data.frame
orders <- load_table("retail.orders")
print(dim(orders))
print(sort(table(orders$region), decreasing = TRUE))
barplot(sort(table(orders$region)), horiz = TRUE, las = 1, main = "Orders by region")
"""


@st.cache_data(show_spinner=False, ttl=3600)
def _tables() -> pd.DataFrame:
    return loader.list_tables()


@st.cache_data(show_spinner=False, ttl=3600)
def _table(schema: str, table: str) -> pd.DataFrame:
    return loader.load_table(schema, table)


def render() -> None:
    st.title(t("Practice & Coding Lab"))
    st.session_state.setdefault("practice_tab", SECTIONS[0])
    section = st.segmented_control(t("Section"), SECTIONS, format_func=t, key="practice_tab", label_visibility="collapsed")
    section = section or SECTIONS[0]
    {
        "SQL workbench": _sql,
        "Python lab": _python,
        "R lab": _r,
        "Coding challenges": _challenges,
        "Dataset explorer": _explorer,
        "Import data": _import,
        "Tool workshops": _tools,
    }[section]()


def _schema_browser() -> None:
    tables = _tables()
    uploads = loader.list_uploads()
    st.markdown(t("**Schemas & tables**"))
    for schema in tables["schema"].unique():
        with st.expander(schema):
            for tbl in tables[tables["schema"] == schema]["table"]:
                doc = table_doc(schema, tbl)
                cols = cached_columns(schema, tbl)
                st.markdown(f"`{schema}.{tbl}`" + (f"  \n:gray[{doc.grain}]" if doc else ""))
                st.caption(", ".join(f"{c} ({d.lower()})" for c, d in zip(cols["column_name"], cols["data_type"])))
    if uploads:
        with st.expander(t("uploads (your files)")):
            for u in uploads:
                st.markdown(f"`uploads.{u}`")


def _sql() -> None:
    st.caption(t("Run read-only DuckDB SQL against every lab dataset. Queries run in a separate process with a timeout; file and network access from SQL is disabled."))
    left, right = st.columns([3, 1])
    with right:
        schema = st.selectbox(t("Default schema"), ["retail", "subscription", "operations", "marketing"], key="sqlw_schema",
                              help=t("Unqualified table names resolve to this schema."))
        _schema_browser()
    with left:
        st.session_state.setdefault("sqlw_code", "SELECT region, COUNT(*) AS orders,\n       ROUND(AVG(shipping_cost), 2) AS avg_shipping\nFROM orders\nWHERE status = 'Completed'\nGROUP BY region\nORDER BY orders DESC;")
        st.text_area("SQL", key="sqlw_code", height=240)
        c1, c2, _ = st.columns([1, 1.4, 3])
        if c1.button(t("Run query"), type="primary", icon=":material/play_arrow:", key="sqlw_run"):
            with st.spinner(t("Running...")):
                st.session_state["sqlw_out"] = run_sql(st.session_state["sqlw_code"], state.run_settings(), schema)
            state.store().log("sql_workbench", schema)
        if c2.button(t("EXPLAIN plan"), key="sqlw_explain", icon=":material/account_tree:"):
            st.session_state["sqlw_out"] = run_sql("EXPLAIN " + st.session_state["sqlw_code"].strip().rstrip(";"), state.run_settings(), schema)
        out = st.session_state.get("sqlw_out")
        if out:
            show_sql_run(out, "sqlw")


def _python() -> None:
    st.caption(t("Free-form Python with pandas, NumPy, SciPy, statsmodels, scikit-learn and Matplotlib. Each run starts fresh in a separate process."))
    st.session_state.setdefault("pyl_code", PY_STARTER)
    st.text_area("Python", key="pyl_code", height=320)
    c1, c2, _ = st.columns([1, 1, 4])
    if c1.button(t("Run"), type="primary", icon=":material/play_arrow:", key="pyl_run"):
        with st.spinner(t("Running...")):
            st.session_state["pyl_out"] = run_python(st.session_state["pyl_code"], state.run_settings())
        state.store().log("python_lab")
    if c2.button(t("Reset"), key="pyl_reset"):
        st.session_state.pop("pyl_code", None)
        st.session_state.pop("pyl_out", None)
        st.rerun()
    out = st.session_state.get("pyl_out")
    if out:
        show_python_run(out, "pyl")


def _r() -> None:
    rs = state.rscript()
    if not rs:
        st.warning(t("R was not found on this computer. Everything else in the lab works without it."))
        st.markdown(t(R_INSTALL_HELP))
        return
    st.caption(t("Using `{rs}`. Plots are captured automatically. Graded R exercises use base R; dplyr/ggplot2 work here if installed.", rs=rs))
    st.session_state.setdefault("rl_code", R_STARTER)
    st.text_area("R", key="rl_code", height=300)
    if st.button(t("Run R"), type="primary", icon=":material/play_arrow:", key="rl_run"):
        with st.spinner(t("Running Rscript...")):
            st.session_state["rl_out"] = run_r(st.session_state["rl_code"], rs, state.run_settings())
        state.store().log("r_lab")
    out = st.session_state.get("rl_out")
    if out:
        show_python_run(out, "rl")


def _challenges() -> None:
    summary = state.store().exercise_summary()
    best = dict(zip(summary["exercise_id"], summary["best_score"])) if not summary.empty else {}
    passed = set(summary[summary["passed"] == 1]["exercise_id"]) if not summary.empty else set()
    c1, c2, c3, c4 = st.columns(4)
    f_mod = c1.multiselect(t("Module"), list(MODULES), format_func=MODULES.get, key="ch_mod")
    f_lang = c2.multiselect(t("Language"), ["sql", "python", "r"], key="ch_lang")
    f_lvl = c3.multiselect(t("Level"), LEVELS, format_func=t, key="ch_lvl")
    f_status = c4.selectbox(t("Status"), ["All", "Not attempted", "Attempted, not passed", "Passed"], format_func=t, key="ch_status")
    exs = [e for e in EXERCISES if (not f_mod or e.module in f_mod) and (not f_lang or e.language in f_lang) and (not f_lvl or e.difficulty in f_lvl)]
    if f_status == "Not attempted":
        exs = [e for e in exs if e.id not in best]
    elif f_status == "Attempted, not passed":
        exs = [e for e in exs if e.id in best and e.id not in passed]
    elif f_status == "Passed":
        exs = [e for e in exs if e.id in passed]
    if not exs:
        st.info(t("No exercises match these filters."))
        return
    ids = [e.id for e in exs]
    if st.session_state.get("challenge_sel") not in ids:
        st.session_state["challenge_sel"] = ids[0]

    def fmt(i: str) -> str:
        e = EXERCISES_BY_ID[i]
        status = " ✅" if i in passed else (f" ({best[i]:.0f})" if i in best else "")
        return f"[{e.language.upper()}] {e.title} · {t(e.difficulty)}{status}"

    st.selectbox(t("Exercise ({n} shown)", n=len(exs)), ids, key="challenge_sel", format_func=fmt)
    with st.container(border=True):
        render_exercise(EXERCISES_BY_ID[st.session_state["challenge_sel"]], prefix="lab")


def _explorer() -> None:
    c1, c2 = st.columns(2)
    schema = c1.selectbox(t("Dataset"), list(DATASETS), format_func=lambda s: f"{DATASETS[s].title} ({s})", key="exp_schema")
    ds = DATASETS[schema]
    table = c2.selectbox(t("Table"), [tb.name for tb in ds.tables], key="exp_table")
    with st.expander(t("Business context, pitfalls and suggested questions"), expanded=False):
        st.markdown(ds.context)
        st.markdown(t("**Known analytical pitfalls**") + "\n" + "\n".join(f"- {p}" for p in ds.pitfalls))
        st.markdown(t("**Suggested questions**") + "\n" + "\n".join(f"- {q}" for q in ds.questions))
        st.caption(t("Reproducible source: `{g}`", g=ds.generator))
    df = _table(schema, table)
    doc = table_doc(schema, table)
    st.markdown(f"**{schema}.{table}** - {doc.description}  \n*{t('Grain')}:* {doc.grain}" + (f" · *{t('Primary key')}:* `{doc.primary_key}`" if doc.primary_key else "")
                + ("".join(f" · *FK* `{c}` -> `{ref}`" for c, ref in doc.foreign_keys.items())))
    m = st.columns(4)
    m[0].metric(t("Rows"), f"{len(df):,}")
    m[1].metric(t("Columns"), df.shape[1])
    m[2].metric(t("Missing cells"), f"{int(df.isna().sum().sum()):,}")
    m[3].metric(t("Duplicate rows"), f"{int(df.duplicated().sum()):,}")
    t1, t2, t3, t4 = st.tabs([t("Sample records"), t("Data dictionary & profile"), t("Charts"), t("Downloads")])
    with t1:
        st.dataframe(df.head(200), hide_index=True, width="stretch")
    with t2:
        prof = loader.profile(df)
        prof.insert(1, "description", prof["column"].map(doc.columns).fillna(""))
        st.dataframe(prof.rename(columns=t), hide_index=True, width="stretch")
    with t3:
        num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c]) and not c.endswith("_id")]
        cat = [c for c in df.columns if (df[c].dtype == object or pd.api.types.is_string_dtype(df[c]) or pd.api.types.is_bool_dtype(df[c])) and df[c].nunique() <= 30]
        a, b = st.columns(2)
        if num:
            col = a.selectbox(t("Numeric column (distribution)"), num, key="exp_num")
            fig = px.histogram(df, x=col, nbins=40, height=320, title=t("Distribution of {col}", col=col))
            fig.update_traces(marker_color="#2563eb")
            a.plotly_chart(fig, key="exp_hist")
            a.plotly_chart(px.box(df, y=col, height=280, points="outliers"), key="exp_box")
        if cat:
            col = b.selectbox(t("Category column (counts)"), cat, key="exp_cat")
            vc = df[col].astype(str).value_counts().reset_index()
            vc.columns = [col, "count"]
            fig = px.bar(vc.sort_values("count"), x="count", y=col, orientation="h", height=320, title=t("Rows by {col}", col=col))
            fig.update_traces(marker_color="#64748b")
            b.plotly_chart(fig, key="exp_bar")
        if len(num) >= 2:
            corr = df[num].corr(numeric_only=True).round(2)
            b.plotly_chart(px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1, height=340, title=t("Correlation matrix")), key="exp_corr")
    with t4:
        st.download_button(t("Download {name}", name=f"{table}.csv"), df.to_csv(index=False).encode(), f"{schema}_{table}.csv", "text/csv", key="exp_dl", icon=":material/download:")
        st.download_button(t("Download {name} data dictionary (.md)", name=ds.title), dataset_markdown(schema), f"{schema}_data_dictionary.md", key="exp_dict")


def _import() -> None:
    st.markdown(t("Import your own **CSV** or **Excel (.xlsx)** file. It is validated, cleaned (column names, numeric/date detection) and stored locally "
                  "as `uploads.<table>` so you can query it in the SQL workbench or explore it here. Nothing leaves your computer."))
    up = st.file_uploader(t("Choose a file"), type=["csv", "txt", "tsv", "xlsx", "xlsm"], key="imp_file")
    if up is not None:
        sheet = 0
        if up.name.lower().endswith((".xlsx", ".xlsm")):
            try:
                import openpyxl
                import io

                names = openpyxl.load_workbook(io.BytesIO(up.getvalue()), read_only=True).sheetnames
                sheet = st.selectbox(t("Worksheet"), names, key="imp_sheet")
            except Exception as exc:
                st.error(t("Could not read the workbook: {exc}", exc=exc))
                return
        res = loader.read_upload(up.name, up.getvalue(), sheet)
        for e in res.errors:
            st.error(e)
        if res.ok:
            for msg in res.messages:
                st.info(msg)
            st.success(t("Parsed {r:,} rows x {c} columns.", r=len(res.frame), c=res.frame.shape[1]))
            st.dataframe(res.frame.head(100), hide_index=True, width="stretch")
            st.dataframe(loader.profile(res.frame).rename(columns=t), hide_index=True, width="stretch")
            name = st.text_input(t("Table name"), res.table_name, key="imp_name")
            if st.button(t("Save as") + " uploads." + loader.sanitize_identifier(name), type="primary", key="imp_save"):
                try:
                    saved = loader.save_upload(name, res.frame)
                    st.success(t("Saved. Query it with `SELECT * FROM uploads.{name}` in the SQL workbench.", name=saved))
                    state.store().log("upload", saved, f"{len(res.frame)} rows")
                except Exception as exc:
                    st.error(t("Could not save the table: {exc}", exc=exc))
    uploads = loader.list_uploads()
    if uploads:
        st.markdown(t("#### Your imported tables"))
        for u in uploads:
            a, b, c = st.columns([3, 1, 1])
            a.markdown(f"`uploads.{u}`")
            if b.button(t("Preview"), key=f"imp_prev_{u}"):
                st.dataframe(loader.load_upload(u).head(100), hide_index=True, width="stretch")
            if c.button(t("Delete"), key=f"imp_del_{u}"):
                loader.drop_upload(u)
                st.rerun()


def _tools() -> None:
    st.caption(t("Practical assignments for Excel, Power BI, Tableau and Looker Studio, plus a dashboard critique. "
                 "The lab does not emulate these products; it provides data, tasks, expected results, simulations and checkers."))
    wid = st.radio(t("Workshop"), list(WORKSHOPS), format_func=lambda w: t(WORKSHOPS[w][0]), key="tools_sel", horizontal=False)
    with st.container(border=True):
        render_workshop(wid, key="lab")
