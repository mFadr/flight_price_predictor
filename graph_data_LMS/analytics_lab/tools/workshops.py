"""Practical workshops for tools the lab cannot run natively (Excel, Power BI,
Tableau, Looker Studio).

The lab never pretends to execute these products. Instead it provides:
* downloadable datasets and briefs to complete the task in the real software,
* expected results computed from the same data so learners can verify their work,
* an Excel workbook checker that reads an uploaded .xlsx (values *and* formulas),
* in-app simulations (PivotTable builder, what-if table, BI model designer, DAX checks).
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass

import numpy as np
import pandas as pd

from analytics_lab.data.loader import load_table, query_df
from analytics_lab.i18n import t

LINES_SQL = """
SELECT o.order_id, o.order_date, o.region, c.segment, cat.category_name AS category, p.product_name,
       oi.product_id, oi.quantity, oi.unit_price, COALESCE(oi.discount_pct, 0) AS discount_pct,
       ROUND(oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0)), 2) AS revenue,
       ROUND(oi.quantity * p.unit_cost, 2) AS cost
FROM retail.orders o
JOIN retail.order_items oi USING (order_id)
JOIN retail.products p USING (product_id)
JOIN retail.categories cat USING (category_id)
JOIN retail.customers c ON c.customer_id = o.customer_id
WHERE o.status = 'Completed' {where}
ORDER BY o.order_date, o.order_id
"""


def completed_lines(where: str = "") -> pd.DataFrame:
    return query_df(LINES_SQL.format(where=where))


# --------------------------------------------------------------------------- #
# Excel workbook workshop                                                       #
# --------------------------------------------------------------------------- #
EXCEL_TASKS = [
    ("B4", "Total revenue of all lines on the Data sheet (add a Revenue column: =Quantity*UnitPrice*(1-Discount)).", "total_revenue"),
    ("B5", "Revenue for the West region (SUMIFS).", "west_revenue"),
    ("B6", "Number of Apparel lines (COUNTIFS).", "apparel_lines"),
    ("B7", "Revenue for Electronics in the Corporate segment (SUMIFS with two criteria).", "corp_electronics"),
    ("B8", "Unit price of product_id 1010 (XLOOKUP or INDEX/MATCH on the Products sheet).", "price_1010"),
    ("B9", "Average order-line revenue in December (AVERAGEIFS with date criteria).", "dec_avg_line"),
    ("B10", "Profit at the scenario price change in Inputs!B2: total revenue * (1 + B2) - total cost (reference the input cell, do not type the value).", "scenario_profit"),
]


def excel_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    lines = completed_lines("AND o.order_date >= DATE '2024-10-01'")
    data = pd.DataFrame(
        {
            "OrderID": lines["order_id"],
            "OrderDate": pd.to_datetime(lines["order_date"]),
            "Region": lines["region"],
            "Segment": lines["segment"],
            "Category": lines["category"],
            "ProductID": lines["product_id"],
            "Quantity": lines["quantity"],
            "UnitPrice": lines["unit_price"],
            "Discount": lines["discount_pct"],
            "Cost": lines["cost"],
        }
    )
    products = load_table("retail", "products")[["product_id", "product_name", "unit_price", "unit_cost"]]
    products.columns = ["ProductID", "ProductName", "UnitPrice", "UnitCost"]
    return data, products


def excel_expected(price_change: float = 0.05) -> dict[str, float]:
    data, products = excel_data()
    rev = data["Quantity"] * data["UnitPrice"] * (1 - data["Discount"])
    return {
        "total_revenue": float(rev.sum()),
        "west_revenue": float(rev[data["Region"] == "West"].sum()),
        "apparel_lines": float((data["Category"] == "Apparel").sum()),
        "corp_electronics": float(rev[(data["Category"] == "Electronics") & (data["Segment"] == "Corporate")].sum()),
        "price_1010": float(products.loc[products["ProductID"] == 1010, "UnitPrice"].iloc[0]),
        "dec_avg_line": float(rev[data["OrderDate"].dt.month == 12].mean()),
        "scenario_profit": float(rev.sum() * (1 + price_change) - data["Cost"].sum()),
    }


def build_excel_workbook() -> bytes:
    """Create the practice workbook (Data, Products, Inputs, Tasks sheets)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    data, products = excel_data()
    wb = Workbook()
    ws = wb.active
    ws.title = "Tasks"
    ws["A1"] = "Northwind Living - Q4 2024 analysis workbook"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = "Enter a FORMULA in each yellow cell (column B). Then save the file in Excel (or LibreOffice) and upload it to the lab checker."
    ws["A3"] = "Task"
    ws["B3"] = "Your formula"
    ws["A3"].font = ws["B3"].font = Font(bold=True)
    fill = PatternFill("solid", fgColor="FFF2CC")
    for cell, text, _ in EXCEL_TASKS:
        row = int(cell[1:])
        ws[f"A{row}"] = text
        ws[cell].fill = fill
    ws.column_dimensions["A"].width = 110
    ws.column_dimensions["B"].width = 22

    inp = wb.create_sheet("Inputs")
    inp["A1"], inp["B1"] = "Assumption", "Value"
    inp["A2"], inp["B2"] = "Scenario price change", 0.05
    inp["A3"] = "Colour code: inputs = blue text. Change B2 and your scenario profit should update automatically."
    inp["B2"].font = Font(color="1F4E79", bold=True)
    inp.column_dimensions["A"].width = 40

    for name, df in (("Data", data), ("Products", products)):
        sh = wb.create_sheet(name)
        sh.append(list(df.columns))
        for row in df.itertuples(index=False):
            sh.append([v.to_pydatetime() if isinstance(v, pd.Timestamp) else (v.item() if hasattr(v, "item") else v) for v in row])
        for i, col in enumerate(df.columns, start=1):
            sh.cell(1, i).font = Font(bold=True)
            sh.column_dimensions[get_column_letter(i)].width = max(12, len(col) + 2)
        if name == "Data":
            for r in range(2, len(df) + 2):
                sh.cell(r, 2).number_format = "yyyy-mm-dd"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@dataclass
class ExcelCheck:
    cell: str
    task: str
    expected: float
    value: float | None
    has_formula: bool
    passed: bool
    message: str


def check_excel_workbook(data: bytes) -> tuple[list[ExcelCheck], list[str]]:
    """Validate an uploaded workbook. Reads cached values (data_only) and formulas."""
    from openpyxl import load_workbook

    notes: list[str] = []
    try:
        wb_vals = load_workbook(io.BytesIO(data), data_only=True)
        wb_form = load_workbook(io.BytesIO(data), data_only=False)
    except Exception as exc:
        return [], [t("Could not open the workbook: {err}. Upload the .xlsx file you saved from Excel.", err=f"{type(exc).__name__}: {exc}")]
    if "Tasks" not in wb_vals.sheetnames:
        return [], [t("The workbook has no 'Tasks' sheet. Start from the downloaded practice workbook.")]
    price_change = 0.05
    if "Inputs" in wb_vals.sheetnames:
        v = wb_vals["Inputs"]["B2"].value
        if isinstance(v, (int, float)):
            price_change = float(v)
    expected = excel_expected(price_change)
    tv, tf = wb_vals["Tasks"], wb_form["Tasks"]
    results = []
    any_cached = False
    for cell, text, key in EXCEL_TASKS:
        val = tv[cell].value
        formula = tf[cell].value
        has_formula = isinstance(formula, str) and formula.startswith("=")
        if isinstance(val, (int, float)):
            any_cached = True
        exp = expected[key]
        if val is None and has_formula:
            ok, msg = False, t("Formula found but no calculated value is stored. Open the file in Excel/LibreOffice, let it calculate, save, and upload again.")
        elif not isinstance(val, (int, float)):
            ok, msg = False, t("No numeric answer in this cell.")
        else:
            ok = bool(np.isclose(float(val), exp, rtol=1e-6, atol=0.01))
            msg = t("Correct.") if ok else t("Expected about {exp:,.2f}, found {val:,.2f}. Check criteria ranges and that discounts are applied.", exp=exp, val=float(val))
            if ok and not has_formula:
                ok, msg = False, t("The value is right but it is typed in. Use a formula so the workbook stays auditable.")
            if key == "scenario_profit" and has_formula and "inputs!" not in formula.lower():
                ok, msg = False, t("Reference the input cell Inputs!B2 instead of typing the price change.")
        results.append(ExcelCheck(cell, text, exp, float(val) if isinstance(val, (int, float)) else None, has_formula, ok, msg))
    if not any_cached:
        notes.append(t("No calculated values were found. Files created by scripts store formulas without results - open and save the workbook in Excel or LibreOffice Calc first."))
    return results, notes


# --------------------------------------------------------------------------- #
# What-if / PivotTable simulations                                               #
# --------------------------------------------------------------------------- #
def what_if_table(prices: list[float], volumes: list[float], unit_cost: float, fixed_cost: float) -> pd.DataFrame:
    """Excel Data Table equivalent: profit for each price (rows) x volume (columns)."""
    grid = np.array([[(p - unit_cost) * v - fixed_cost for v in volumes] for p in prices])
    return pd.DataFrame(grid, index=pd.Index(prices, name="price"), columns=pd.Index(volumes, name="volume"))


def goal_seek_price(target_profit: float, volume: float, unit_cost: float, fixed_cost: float) -> float:
    """Analytical Goal Seek: price that yields target profit at a fixed volume."""
    return unit_cost + (target_profit + fixed_cost) / volume


# --------------------------------------------------------------------------- #
# Power BI model designer & DAX checks                                           #
# --------------------------------------------------------------------------- #
PBI_TABLES = {
    "order_items": ("Fact", "One row per order line with quantity, price and discount."),
    "orders": ("Dimension", "Order header attributes (date, region, status). Often merged into the fact or used as a degenerate dimension."),
    "products": ("Dimension", "Product attributes incl. category and cost."),
    "categories": ("Dimension", "Category lookup (can be merged into products)."),
    "customers": ("Dimension", "Customer attributes (segment, signup date)."),
    "Calendar": ("Dimension", "One row per date; marked as date table for time intelligence."),
}
PBI_RELATIONSHIPS = [
    # (from table, to table, correct cardinality, correct direction)
    ("products", "order_items", "One-to-many", "Single"),
    ("orders", "order_items", "One-to-many", "Single"),
    ("customers", "orders", "One-to-many", "Single"),
    ("Calendar", "orders", "One-to-many", "Single"),
    ("categories", "products", "One-to-many", "Single"),
]


@dataclass
class DaxQuestion:
    prompt: str
    options: list[str]
    correct: int
    explanation: str


def dax_questions() -> list[DaxQuestion]:
    """Questions whose answers are computed from the data, so they match what Power BI would show."""
    lines = completed_lines()
    lines["order_date"] = pd.to_datetime(lines["order_date"])
    west24 = lines[(lines["region"] == "West") & (lines["order_date"].dt.year == 2024)]
    m = (west24["revenue"].sum() - west24["cost"].sum()) / west24["revenue"].sum()
    avg_row = ((west24["revenue"] - west24["cost"]) / west24["revenue"]).mean()
    y24 = lines[lines["order_date"].dt.year == 2024]
    ytd_jun = y24[y24["order_date"].dt.month <= 6]["revenue"].sum()
    jun = y24[y24["order_date"].dt.month == 6]["revenue"].sum()
    total24 = y24["revenue"].sum()
    q1 = DaxQuestion(
        t("Slicers: Region = West, Year = 2024. Card visual shows `Margin % = DIVIDE([Revenue] - [Cost], [Revenue])`. What value does it display?"),
        [f"{m:.1%}", f"{avg_row:.1%}", f"{m * 1.1:.1%}", f"{(lines['revenue'].sum() - lines['cost'].sum()) / lines['revenue'].sum() + 0.03:.1%}"],
        0,
        t("The measure divides the summed components in the current filter context ({m:.1%}). Averaging row-level margins would give {avg:.1%} - a different, wrong number.", m=m, avg=avg_row),
    )
    q2 = DaxQuestion(
        t("A table visual shows Month (2024) and `Revenue YTD = TOTALYTD([Revenue], 'Calendar'[Date])`. What is shown for June 2024?"),
        [f"EUR {ytd_jun:,.0f}", f"EUR {jun:,.0f}", f"EUR {total24:,.0f}", f"EUR {ytd_jun / 6:,.0f}"],
        0,
        t("TOTALYTD accumulates from 1 January to the end of the current month in context."),
    )
    q3 = DaxQuestion(
        t("With Region = West selected in a slicer, what does `West share = DIVIDE([Revenue], CALCULATE([Revenue], ALL(orders[region])))` show for 2024?"),
        [f"{west24['revenue'].sum() / total24:.1%}", "100.0%", f"{1 / 5:.1%}", f"{west24['revenue'].sum() / lines['revenue'].sum():.1%}"],
        0,
        t("ALL(orders[region]) removes the region filter in the denominator while the year filter remains, giving West's share of 2024 revenue."),
    )
    return [q1, q2, q3]


def powerbi_expected() -> pd.DataFrame:
    lines = completed_lines()
    lines["year"] = pd.to_datetime(lines["order_date"]).dt.year
    g = lines.groupby("year").agg(revenue=("revenue", "sum"), cost=("cost", "sum"), orders=("order_id", "nunique"))
    g["margin_pct"] = (g["revenue"] - g["cost"]) / g["revenue"] * 100
    g["aov"] = g["revenue"] / g["orders"]
    return g.round(2).reset_index()


# --------------------------------------------------------------------------- #
# Tableau & Looker Studio packs                                                  #
# --------------------------------------------------------------------------- #
def retail_csv_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for tbl in ("orders", "order_items", "products", "categories", "customers", "returns"):
            z.writestr(f"{tbl}.csv", load_table("retail", tbl).to_csv(index=False))
    return buf.getvalue()


def looker_flat_csv() -> bytes:
    lines = completed_lines("AND YEAR(o.order_date) = 2024")
    return lines.to_csv(index=False).encode("utf-8")


def bi_expected_values() -> dict[str, object]:
    """Numbers learners should reproduce in Tableau / Looker Studio for 2024 completed orders."""
    lines = completed_lines("AND YEAR(o.order_date) = 2024")
    by_cat = lines.groupby("category").agg(revenue=("revenue", "sum"), cost=("cost", "sum"))
    by_cat["margin_pct"] = (by_cat["revenue"] - by_cat["cost"]) / by_cat["revenue"] * 100
    by_reg = lines.groupby("region")["revenue"].sum().sort_values(ascending=False)
    return {
        "revenue": lines["revenue"].sum(),
        "orders": lines["order_id"].nunique(),
        "aov": lines["revenue"].sum() / lines["order_id"].nunique(),
        "margin_pct": (lines["revenue"].sum() - lines["cost"].sum()) / lines["revenue"].sum() * 100,
        "by_category": by_cat.round(2).sort_values("revenue", ascending=False).reset_index(),
        "by_region": by_reg.round(2).reset_index(),
    }


TABLEAU_TASKS = [
    "Connect to the CSV files and create relationships: order_items-orders (order_id), order_items-products (product_id), products-categories (category_id), orders-customers (customer_id).",
    "Create calculated fields: Revenue = [Quantity] * [Unit Price] * (1 - ZN([Discount Pct])); Line Cost = [Quantity] * [Unit Cost]; Completed Revenue = IF [Status] = 'Completed' THEN [Revenue] END.",
    "Sheet 'Trend': continuous MONTH(Order Date) vs SUM(Completed Revenue) for 2024; add a reference line for the average.",
    "Sheet 'Category margin': Margin % = (SUM([Completed Revenue]) - SUM([Completed Cost])) / SUM([Completed Revenue]); sorted bars.",
    "Sheet 'Regions': SUM(Completed Revenue) by Region, sorted, labelled.",
    "LOD: First Order = { FIXED [Customer Id] : MIN([Order Date]) }; show customers by first-order quarter.",
    "Dashboard: combine the sheets; Year and Region filters applied to all worksheets; a filter action from Category to Trend.",
]
LOOKER_TASKS = [
    "Upload looker_retail_lines.csv (Create -> Data source -> File upload) or import it into Google Sheets.",
    "In the data source: order_date = Date; revenue & cost = Currency (EUR), aggregation Sum; order_id used with Count Distinct.",
    "Calculated fields: Gross margin % = (SUM(revenue) - SUM(cost)) / SUM(revenue); AOV = SUM(revenue) / COUNT_DISTINCT(order_id).",
    "Scorecards: Revenue, Orders, AOV, Gross margin % (compare to previous period).",
    "Time series of revenue by month; bar chart of revenue by category (sorted); table by region.",
    "Controls: date range, region drop-down, category drop-down; enable cross-filtering.",
    "Add a text box with the KPI definitions and data source/freshness; share as viewer only.",
]
SELF_CHECK = [
    "My totals match the expected values shown in the lab (within rounding).",
    "Ratios (margin %, AOV) are computed from sums, not averaged.",
    "Every chart has a clear title and labelled axes/units.",
    "Filters/controls apply to all intended visuals.",
    "Definitions and data source are documented on the dashboard.",
]
