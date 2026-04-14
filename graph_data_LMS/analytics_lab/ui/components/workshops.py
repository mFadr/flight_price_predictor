"""UI for tool workshops (Excel, Power BI, Tableau, Looker Studio, chart critique)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from analytics_lab.assessment.cases import CRITIQUE_FLAWS, misleading_dashboard_png
from analytics_lab.data.catalog import dataset_markdown
from analytics_lab.i18n import get_lang, t
from analytics_lab.tools import workshops as ws
from analytics_lab.ui import state

WORKSHOPS = {
    "excel_workbook": ("Excel: auditable workbook, PivotTables & what-if", "descriptive"),
    "powerbi_model": ("Power BI: data model designer & DAX checks", "descriptive"),
    "tableau": ("Tableau: guided workbook assignment", "visualization"),
    "looker": ("Looker Studio: guided report assignment", "visualization"),
    "chart_critique": ("Dashboard critique: find the misleading elements", "visualization"),
}

NOT_NATIVE = ("This workshop does **not** run {tool} inside the lab. You complete the task in the real software (or the in-app simulation), "
              "and the lab provides data, instructions and expected results so you can verify your work.")


EXCEL_STEPS = """
1. Download the practice workbook (Q4 2024 completed order lines, products and an Inputs sheet).
2. Open it in **Excel** (or LibreOffice Calc), and enter a **formula** in each yellow cell of the *Tasks* sheet.
3. Save and upload it below. The checker reads both the calculated values and the formulas: typed-in numbers do not count, and the scenario profit must reference `Inputs!B2`.
"""


PBI_STEPS = """
**Task (Power BI Desktop, free for Windows):**
1. *Get Data -> Text/CSV*: load `orders`, `order_items`, `products`, `categories`, `customers` from the download below.
2. In Power Query: set data types, filter `orders[status] = "Completed"`, merge `categories` into `products`.
3. Create a `Calendar` table: `Calendar = CALENDAR(DATE(2023,1,1), DATE(2024,12,31))`, mark it as date table, relate to `orders[order_date]`.
4. Create measures: Revenue, Cost, Margin %, Orders, AOV, Revenue YTD, Revenue PY, YoY % (see the DAX cheat sheet).
5. Build one page: KPI cards (Revenue, Margin %, AOV, YoY %), revenue trend by month, revenue by category (sorted bar), region slicer, drill-down Year -> Month.
6. Verify your card values against the expected results below, then tick the self-check.
"""


@st.cache_data(show_spinner=False)
def _excel_bytes() -> bytes:
    return ws.build_excel_workbook()


@st.cache_data(show_spinner=False)
def _excel_expected() -> dict:
    return ws.excel_expected()


@st.cache_data(show_spinner=False)
def _lines() -> pd.DataFrame:
    df = ws.completed_lines()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["year"] = df["order_date"].dt.year
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    return df


@st.cache_data(show_spinner=False)
def _bi_expected() -> dict:
    return ws.bi_expected_values()


@st.cache_data(show_spinner=False)
def _zip() -> bytes:
    return ws.retail_csv_zip()


@st.cache_data(show_spinner=False)
def _looker_csv() -> bytes:
    return ws.looker_flat_csv()


@st.cache_data(show_spinner=False)
def _dax(lang: str):
    return ws.dax_questions()


@st.cache_data(show_spinner=False)
def _critique_png() -> bytes:
    return misleading_dashboard_png()


def render_workshop(wid: str, key: str = "ws") -> None:
    {"excel_workbook": _excel, "powerbi_model": _powerbi, "tableau": _tableau, "looker": _looker, "chart_critique": _critique}[wid](key)


def _task_status(task_id: str) -> str | None:
    t = state.store().tool_tasks()
    row = t[t["task_id"] == task_id]
    return None if row.empty else f"{t(row.iloc[0]['status'])} ({row.iloc[0]['score']:.0f}%)" if pd.notna(row.iloc[0]["score"]) else t(row.iloc[0]["status"])


# --------------------------------------------------------------------------- Excel
def _excel(key: str) -> None:
    st.markdown(t(NOT_NATIVE, tool="Microsoft Excel"))
    t1, t2, t3 = st.tabs([t("Workbook assignment (graded)"), t("PivotTable simulator"), t("What-if simulator")])
    with t1:
        st.markdown(t(EXCEL_STEPS))
        st.download_button(t("Download practice workbook (.xlsx)"), _excel_bytes(), "northwind_q4_2024_workbook.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{key}_xl_dl", icon=":material/download:")
        status = _task_status("excel_workbook")
        if status:
            st.caption(t("Your last result: {s}", s=status))
        up = st.file_uploader(t("Upload your completed workbook"), type=["xlsx"], key=f"{key}_xl_up")
        if up is not None:
            results, notes = ws.check_excel_workbook(up.getvalue())
            for n in notes:
                st.warning(n)
            if results:
                df = pd.DataFrame([{t("Cell"): r.cell, t("Task"): t(r.task), t("Your value"): r.value, t("Formula?"): t("yes") if r.has_formula else t("no"),
                                    t("Result"): "✔" if r.passed else "✘", t("Feedback"): r.message} for r in results])
                st.dataframe(df, hide_index=True, width="stretch")
                score = 100 * sum(r.passed for r in results) / len(results)
                (st.success if score == 100 else st.info)(t("Score: {s:.0f}% ({n}/{total} tasks)", s=score, n=sum(r.passed for r in results), total=len(results)))
                if st.button(t("Save result to my progress"), key=f"{key}_xl_save"):
                    state.store().set_tool_task("excel_workbook", "completed" if score == 100 else "attempted", score, f"{score:.0f}%")
                    st.toast(t("Saved."))
        with st.expander(t("Formula hints")):
            st.markdown(t("""
* Add a column K `Revenue` on the Data sheet: `=G2*H2*(1-I2)` and fill down (or convert to a Table and use `=[@Quantity]*[@UnitPrice]*(1-[@Discount])`).
* `=SUMIFS(Data!K:K, Data!C:C, "West")`  ·  `=COUNTIFS(Data!E:E, "Apparel")`
* `=SUMIFS(Data!K:K, Data!E:E, "Electronics", Data!D:D, "Corporate")`
* `=XLOOKUP(1010, Products!A:A, Products!C:C)` or `=INDEX(Products!C:C, MATCH(1010, Products!A:A, 0))`
* `=AVERAGEIFS(Data!K:K, Data!B:B, ">="&DATE(2024,12,1), Data!B:B, "<"&DATE(2025,1,1))`
* `=B4*(1+Inputs!B2)-SUM(Data!J:J)`
"""))
    with t2:
        df = _lines()
        st.markdown(t("A PivotTable is a GROUP BY with drag-and-drop. Choose fields as you would in Excel's PivotTable Fields pane (completed order lines, 2023-2024)."))
        c1, c2, c3, c4 = st.columns(4)
        rows = c1.selectbox(t("Rows"), ["region", "category", "segment", "year", "month"], key=f"{key}_pv_rows")
        cols = c2.selectbox(t("Columns"), ["(none)", "year", "segment", "region", "category"], key=f"{key}_pv_cols")
        val = c3.selectbox(t("Values"), ["revenue", "cost", "quantity", "order_id"], key=f"{key}_pv_val")
        agg = c4.selectbox(t("Summarise by"), ["sum", "mean", "count", "nunique"], key=f"{key}_pv_agg")
        flt = st.multiselect(t("Filter: region"), sorted(df["region"].unique()), key=f"{key}_pv_flt")
        d = df[df["region"].isin(flt)] if flt else df
        if cols != "(none)" and cols != rows:
            pv = pd.pivot_table(d, index=rows, columns=cols, values=val, aggfunc=agg, margins=True, margins_name="Grand Total")
        else:
            pv = d.groupby(rows)[val].agg(agg).to_frame(f"{agg} of {val}")
        st.dataframe(pv.round(2), width="stretch")
        st.code(f"=SUMIFS(Data[{val}], Data[{rows}], <row item>{', Data[' + cols + '], <column item>' if cols != '(none)' else ''})   -- " + t("equivalent cell formula (for sum)"), language="text")
        if st.button(t("Mark PivotTable simulation explored"), key=f"{key}_pv_done"):
            state.store().set_tool_task("excel_pivot", "completed", 100)
            st.toast(t("Recorded."))
    with t3:
        st.markdown(t("Excel's **Data Table** shows an output for a grid of inputs; **Goal Seek** finds the input that hits a target."))
        c1, c2, c3 = st.columns(3)
        unit_cost = c1.number_input(t("Unit cost (EUR)"), 1.0, 500.0, 12.0, key=f"{key}_wi_cost")
        fixed = c2.number_input(t("Fixed cost (EUR)"), 0.0, 1e6, 8000.0, step=500.0, key=f"{key}_wi_fixed")
        target = c3.number_input(t("Goal Seek: target profit"), 0.0, 1e6, 10000.0, step=500.0, key=f"{key}_wi_target")
        prices = [16.0, 18.0, 20.0, 22.0, 24.0]
        volumes = [800, 1000, 1200, 1400, 1600]
        tbl = ws.what_if_table(prices, volumes, unit_cost, fixed)
        st.dataframe(tbl.style.format("{:,.0f}").background_gradient(cmap="RdYlGn", axis=None), width="stretch")
        vol = st.slider(t("Volume for Goal Seek"), 200, 3000, 1200, 100, key=f"{key}_wi_vol")
        st.metric(t("Price needed"), f"EUR {ws.goal_seek_price(target, vol, unit_cost, fixed):,.2f}")


# --------------------------------------------------------------------------- Power BI
def _powerbi(key: str) -> None:
    st.markdown(t(NOT_NATIVE, tool="Power BI Desktop"))
    t1, t2, t3 = st.tabs([t("Model designer (graded)"), t("DAX filter-context check (graded)"), t("Power BI Desktop assignment")])
    with t1:
        st.markdown(t("Classify each table and configure the relationships as you would in Power BI's *Model view*."))
        with st.form(f"{key}_pbi_form"):
            roles = {}
            cols = st.columns(3)
            for i, (tbl, (_, desc)) in enumerate(ws.PBI_TABLES.items()):
                roles[tbl] = cols[i % 3].radio(f"`{tbl}`", ["Fact", "Dimension"], format_func=t, index=None, key=f"{key}_role_{tbl}", help=t(desc))
            st.markdown(t("**Relationships**"))
            rels = {}
            for a, b, _, _ in ws.PBI_RELATIONSHIPS:
                c1, c2, c3 = st.columns([2, 1.5, 1.5])
                c1.markdown(f"`{a}` -> `{b}`")
                card = c2.selectbox(t("Cardinality"), ["One-to-many", "Many-to-many", "One-to-one"], format_func=t, index=None, key=f"{key}_card_{a}_{b}", label_visibility="collapsed", placeholder=t("Cardinality"))
                direc = c3.selectbox(t("Filter direction"), ["Single", "Both"], format_func=t, index=None, key=f"{key}_dir_{a}_{b}", label_visibility="collapsed", placeholder=t("Direction"))
                rels[(a, b)] = (card, direc)
            ok = st.form_submit_button(t("Check model"), type="primary")
        if ok:
            pts, total, msgs = 0, 0, []
            for tbl, (role, desc) in ws.PBI_TABLES.items():
                total += 1
                if roles[tbl] == role:
                    pts += 1
                else:
                    msgs.append(t("✘ `{tbl}` should be a **{role}** table - {desc}", tbl=tbl, role=t(role), desc=t(desc)))
            for a, b, card, direc in ws.PBI_RELATIONSHIPS:
                total += 2
                c, d = rels[(a, b)]
                pts += (c == card) + (d == direc)
                if c != card:
                    msgs.append(t("✘ `{a}` -> `{b}` is **{card}**: each `{a}` row matches many `{b}` rows.", a=a, b=b, card=t(card)))
                if d != direc:
                    msgs.append(t("✘ `{a}` -> `{b}` should filter in a **{direc}** direction (dimension filters fact); bi-directional filters create ambiguity.", a=a, b=b, direc=t(direc)))
            score = 100 * pts / total
            (st.success if score == 100 else st.warning)(t("Score {s:.0f}% ({n}/{total})", s=score, n=pts, total=total))
            for m in msgs:
                st.markdown(m)
            state.store().set_tool_task("powerbi_model", "completed" if score == 100 else "attempted", score)
    with t2:
        qs = _dax(get_lang())
        with st.form(f"{key}_dax_form"):
            answers = [st.radio(q.prompt, q.options, index=None, key=f"{key}_dax_{i}") for i, q in enumerate(qs)]
            ok = st.form_submit_button(t("Check"), type="primary")
        if ok:
            n = 0
            for q, a in zip(qs, answers):
                good = a == q.options[q.correct]
                n += good
                (st.success if good else st.error)((t("Correct.") + " " if good else t("Answer: {a}.", a=q.options[q.correct]) + " ") + q.explanation)
            state.store().set_tool_task("dax_check", "completed" if n == len(qs) else "attempted", 100 * n / len(qs))
    with t3:
        st.markdown(t(PBI_STEPS))
        st.download_button(t("Download retail CSVs (.zip)"), _zip(), "northwind_retail_csv.zip", "application/zip", key=f"{key}_pbi_zip", icon=":material/download:")
        st.download_button(t("Download data dictionary (.md)"), dataset_markdown("retail"), "retail_data_dictionary.md", key=f"{key}_pbi_dict")
        st.markdown(t("**Expected results (completed orders)** - your Power BI cards should match:"))
        st.dataframe(ws.powerbi_expected().rename(columns=t), hide_index=True, width="stretch")
        _self_check("powerbi_assignment", key)


# --------------------------------------------------------------------------- Tableau / Looker
def _expected_block() -> None:
    e = _bi_expected()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("2024 revenue"), f"EUR {e['revenue']:,.0f}")
    c2.metric(t("Orders"), f"{e['orders']:,}")
    c3.metric("AOV", f"EUR {e['aov']:,.2f}")
    c4.metric(t("Gross margin"), f"{e['margin_pct']:.1f}%")
    a, b = st.columns(2)
    a.dataframe(e["by_category"].rename(columns=t), hide_index=True, width="stretch")
    b.dataframe(e["by_region"].rename(columns=t), hide_index=True, width="stretch")


def _self_check(task_id: str, key: str) -> None:
    st.markdown(t("**Self-check** (recorded as self-assessed, not automatically verified)"))
    checks = [st.checkbox(t(c), key=f"{key}_{task_id}_sc{i}") for i, c in enumerate(ws.SELF_CHECK)]
    if st.button(t("Save self-check"), key=f"{key}_{task_id}_save"):
        score = 100 * sum(checks) / len(checks)
        state.store().set_tool_task(task_id, "completed" if score == 100 else "attempted", score, "self-assessed")
        st.toast(t("Saved ({s:.0f}%).", s=score))
    status = _task_status(task_id)
    if status:
        st.caption(t("Last saved: {s}", s=status))


def _tableau(key: str) -> None:
    st.markdown(t(NOT_NATIVE, tool="Tableau"))
    st.markdown(t("Use **Tableau Desktop** or the free **Tableau Public**. Complete the tasks, then compare your numbers with the expected values (2024, completed orders)."))
    st.download_button(t("Download retail CSVs (.zip)"), _zip(), "northwind_retail_csv.zip", "application/zip", key=f"{key}_tab_zip", icon=":material/download:")
    st.markdown("\n".join(f"{i}. {t(task)}" for i, task in enumerate(ws.TABLEAU_TASKS, 1)))
    st.markdown(t("#### Expected values"))
    _expected_block()
    _self_check("tableau_assignment", key)


def _looker(key: str) -> None:
    st.markdown(t(NOT_NATIVE, tool="Looker Studio"))
    st.markdown(t("Looker Studio is free and browser-based (Google account required). This lab does not connect to Google - upload the prepared file yourself."))
    st.download_button(t("Download {name}", name="looker_retail_lines.csv"), _looker_csv(), "looker_retail_lines.csv", "text/csv", key=f"{key}_lk_csv", icon=":material/download:")
    st.markdown("\n".join(f"{i}. {t(task)}" for i, task in enumerate(ws.LOOKER_TASKS, 1)))
    st.markdown(t("#### Expected scorecards"))
    _expected_block()
    _self_check("looker_assignment", key)


# --------------------------------------------------------------------------- Chart critique
def _critique(key: str) -> None:
    st.markdown(t("This dashboard was shown to executives during the West region's stock-out. Identify every misleading or problematic element."))
    st.image(_critique_png(), width="stretch")
    st.caption(t("Analyst's note: pie-chart revenue was summed from list prices; period shown is March-October 2024."))
    options = [f[0] for f in CRITIQUE_FLAWS]
    with st.form(f"{key}_crit_form"):
        chosen = st.multiselect(t("Select all problems you can find"), options, format_func=t, key=f"{key}_crit_sel")
        fixes = st.text_area(t("For each problem: what effect does it have, and how would you fix it?"), key=f"{key}_crit_fix", height=150)
        ok = st.form_submit_button(t("Check"), type="primary")
    if ok:
        truth = {f[0] for f in CRITIQUE_FLAWS if f[1]}
        hits = truth & set(chosen)
        false_pos = set(chosen) - truth
        score = max(0.0, 100 * (len(hits) - len(false_pos)) / len(truth))
        (st.success if score == 100 else st.warning)(t("Found {h}/{n} genuine problems; {fp} incorrect selection(s). Score {s:.0f}%.", h=len(hits), n=len(truth), fp=len(false_pos), s=score))
        for f, real in CRITIQUE_FLAWS:
            if real and f not in chosen:
                st.markdown(t("- Missed: **{f}**", f=t(f)))
            if not real and f in chosen:
                st.markdown(t("- Not a problem: *{f}*", f=t(f)))
        st.info(t("Model fixes: monthly (not cumulative) revenue with zero baseline and an annotation; two aligned panels instead of dual axes; "
                  "bars from zero; sorted horizontal bars with direct labels instead of the pie; axis labels with units; one consistent revenue definition; a neutral, finding-based title."))
        state.store().set_tool_task("chart_critique", "completed" if score == 100 else "attempted", score, fixes[:500])
