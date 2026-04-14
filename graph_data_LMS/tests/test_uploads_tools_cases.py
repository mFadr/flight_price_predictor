"""User uploads, tool workshops (Excel checker, Power BI) and business-case scoring."""

import io

import pandas as pd
from openpyxl import Workbook, load_workbook

from analytics_lab.assessment import cases
from analytics_lab.data import loader
from analytics_lab.execution.runners import run_sql
from analytics_lab.tools import workshops as ws


# ------------------------------------------------------------------ uploads
def test_csv_upload_semicolon_and_cleaning():
    rows = "".join(f"2024-01-{d:02d};{d * 100};West\n" for d in range(1, 21))
    data = ("Order Date;Amount (EUR);Region\n2024-01-21;1,200;East\n2024-01-22;abc;East\n2024-01-23;300;\n" + rows).encode()
    res = loader.read_upload("My Sales.csv", data)
    assert res.ok, res.errors
    assert res.table_name == "my_sales"
    assert list(res.frame.columns) == ["order_date", "amount_eur", "region"]
    assert pd.api.types.is_numeric_dtype(res.frame["amount_eur"])
    assert res.frame["amount_eur"].iloc[0] == 1200  # thousands separator handled
    assert pd.api.types.is_datetime64_any_dtype(res.frame["order_date"])
    assert any("non-numeric" in m for m in res.messages)
    assert any("missing" in m for m in res.messages)


def test_bad_uploads_give_helpful_errors():
    assert "empty" in loader.read_upload("a.csv", b"").errors[0]
    assert "Unsupported" in loader.read_upload("a.pdf", b"%PDF").errors[0]
    assert loader.read_upload("a.xlsx", b"not really excel").errors
    assert "xlsx" in loader.read_upload("old.xls", b"x").errors[0]


def test_excel_upload_and_sql_query():
    wb = Workbook()
    wb.active.append(["Product", "Units"])
    wb.active.append(["A", 3])
    wb.active.append(["B", 5])
    buf = io.BytesIO()
    wb.save(buf)
    res = loader.read_upload("stock.xlsx", buf.getvalue())
    assert res.ok
    name = loader.save_upload("stock", res.frame)
    assert name in loader.list_uploads()
    r = run_sql("SELECT SUM(units) AS total FROM uploads.stock")
    assert r.ok and r.frame.iloc[0, 0] == 8
    loader.drop_upload("stock")
    assert "stock" not in loader.list_uploads()


# ------------------------------------------------------------------ Excel workshop
def test_practice_workbook_structure():
    wb = load_workbook(io.BytesIO(ws.build_excel_workbook()))
    assert {"Tasks", "Inputs", "Data", "Products"} <= set(wb.sheetnames)
    assert wb["Data"].max_row > 1000


def test_checker_rejects_typed_values_and_uncalculated_formulas():
    exp = ws.excel_expected()
    wb = load_workbook(io.BytesIO(ws.build_excel_workbook()))
    wb["Tasks"]["B4"] = exp["total_revenue"]       # typed value -> not auditable
    wb["Tasks"]["B5"] = "=SUMIFS(Data!K:K,Data!C:C,\"West\")"  # formula without cached value
    buf = io.BytesIO()
    wb.save(buf)
    results, notes = ws.check_excel_workbook(buf.getvalue())
    by_cell = {r.cell: r for r in results}
    assert not by_cell["B4"].passed and "typed in" in by_cell["B4"].message
    assert not by_cell["B5"].passed and "calculated value" in by_cell["B5"].message


def test_checker_handles_garbage():
    results, notes = ws.check_excel_workbook(b"garbage")
    assert not results and notes


def test_expected_values_are_consistent():
    exp = ws.excel_expected(0.0)
    data, _ = ws.excel_data()
    assert abs(exp["scenario_profit"] - (exp["total_revenue"] - data["Cost"].sum())) < 1e-6
    assert ws.goal_seek_price(1000, 100, 5, 500) == 20


def test_dax_questions_have_unique_correct_answers():
    for q in ws.dax_questions():
        assert len(set(q.options)) == len(q.options) and 0 <= q.correct < len(q.options)


def test_bi_expected_values():
    e = ws.bi_expected_values()
    assert e["revenue"] > 0 and abs(e["by_category"]["revenue"].sum() - e["revenue"]) < 1


# ------------------------------------------------------------------ business cases
def test_case_evidence_builders_run():
    for c in cases.CASES:
        blocks = cases.EVIDENCE_BUILDERS[c.evidence_builder]()
        assert blocks and all(kind in ("md", "table", "img") for kind, _ in blocks)


def test_case_scoring_is_transparent():
    c = cases.CASES_BY_ID["case_revenue_decline"]
    obj, res = cases.score_objectives(c, [o.correct for o in c.objectives])
    assert obj == 100 and all(res)
    obj2, _ = cases.score_objectives(c, [[0], [3], [0]])
    assert obj2 == 0
    levels = {cr.name: 3 for cr in c.rubric}
    assert cases.score_self_assessment(c.rubric, levels) == 100
    assert cases.combined_score(100, 50) == 75
    cov = cases.keyword_coverage(c.rubric, "We recommend checking inventory; an alternative is a promotion.")
    assert "recommend" in cov["Business relevance"]
