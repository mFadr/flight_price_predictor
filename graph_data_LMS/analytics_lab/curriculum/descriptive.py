"""Module 1 - Descriptive Analytics (SQL, Excel, Power BI)."""

from analytics_lab.models import Lesson, WorkedExample

REVENUE_NOTE = "Revenue throughout the lab = `quantity * unit_price * (1 - COALESCE(discount_pct, 0))` on order lines of **Completed** orders."

LESSONS = [
    Lesson(
        id="ds1",
        module="descriptive",
        level="Beginner",
        title="SQL foundations: selecting, filtering and summarising",
        tools=["SQL"],
        minutes=35,
        competencies=["sql_basics", "kpi_reporting"],
        objectives=[
            "Read a table schema and pick the columns that answer a question.",
            "Filter rows with WHERE, including dates, text and multiple conditions.",
            "Sort and limit results with ORDER BY and LIMIT; remove duplicates with DISTINCT.",
            "Summarise a whole table with COUNT, SUM, AVG, MIN and MAX.",
        ],
        concept="""
SQL is a *declarative* language: you describe **what** result you want and the database works out **how** to compute it.
A query is evaluated in a logical order that differs from the order you type it:

| Logical step | Clause | What it does |
|---|---|---|
| 1 | `FROM` | choose the table(s) |
| 2 | `WHERE` | keep only rows that meet a condition |
| 3 | `GROUP BY` | form groups (next lesson) |
| 4 | `HAVING` | filter groups (next lesson) |
| 5 | `SELECT` | compute the output columns |
| 6 | `ORDER BY` | sort the output |
| 7 | `LIMIT` | keep the first *n* rows |

Key ideas:

* `WHERE status = 'Completed'` compares text exactly (case-sensitive in DuckDB). Use `IN ('A','B')` for lists and `BETWEEN` or `>=`/`<` for ranges.
* For dates, prefer half-open ranges: `order_date >= DATE '2024-01-01' AND order_date < DATE '2025-01-01'`. They work with timestamps too.
* `COUNT(*)` counts rows; `COUNT(col)` counts **non-NULL** values; `COUNT(DISTINCT col)` counts unique non-NULL values.
* `AVG`, `SUM`, `MIN` and `MAX` ignore NULLs, which can silently change the meaning of an average.
* `DISTINCT` applies to the **whole selected row**, not just the first column.
""",
        business_context="""
Northwind Living's finance team asks: *"How many completed orders did we process in 2024, from how many customers, and what did customers pay for shipping on average?"*
These headline numbers open every monthly business review. Getting them wrong (for example, by counting cancelled orders) erodes trust in every number that follows.
""",
        worked_example=WorkedExample(
            language="sql",
            search_path="retail",
            code="""-- Headline order statistics for 2024 (completed orders only)
SELECT
    COUNT(*)                     AS completed_orders,
    COUNT(DISTINCT customer_id)  AS distinct_customers,
    ROUND(AVG(shipping_cost), 2) AS avg_shipping_fee,
    MIN(order_date)              AS first_order,
    MAX(order_date)              AS last_order
FROM orders
WHERE status = 'Completed'
  AND order_date >= DATE '2024-01-01'
  AND order_date <  DATE '2025-01-01';""",
            explanation="""
1. `FROM orders` - order headers, one row per order (check the grain in the schema panel).
2. `WHERE` keeps only completed orders placed in 2024, using a half-open date range.
3. `COUNT(*)` counts orders; `COUNT(DISTINCT customer_id)` counts unique buyers - a customer with five orders counts once.
4. `ROUND(AVG(...), 2)` makes the output readable without changing the underlying calculation.

**Validate:** remove the `status` filter and compare - the difference is the cancelled and pending orders you deliberately excluded.
""",
        ),
        extra_examples=[
            WorkedExample(
                language="sql",
                search_path="retail",
                code="""-- Ten most expensive products, with DISTINCT and LIMIT in action
SELECT product_id, product_name, unit_price
FROM products
ORDER BY unit_price DESC
LIMIT 10;

-- Which regions exist? (run separately)
-- SELECT DISTINCT region FROM orders ORDER BY region;""",
                explanation="`ORDER BY ... DESC LIMIT 10` is the standard *top-N* pattern. Without ORDER BY, LIMIT returns an arbitrary 10 rows.",
            )
        ],
        knowledge_check=["q_ds_001", "q_ds_002", "q_ds_003"],
        guided_exercise="ex_sql_ds1_top_products",
        challenge="ex_sql_ds1_headline",
        summary=[
            "SQL runs FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY -> LIMIT.",
            "Use half-open date ranges and explicit status filters for KPIs.",
            "COUNT(*), COUNT(col) and COUNT(DISTINCT col) answer different questions.",
            "Aggregates ignore NULLs - check whether that matches the business meaning.",
        ],
        common_mistakes=[
            "Counting all orders instead of completed ones.",
            "Using `order_date BETWEEN '2024-01-01' AND '2024-12-31'` on timestamps and missing the last day.",
            "Using LIMIT without ORDER BY and assuming the rows are the 'top' ones.",
        ],
        revision="Revisit the clause-order table and rerun the worked example removing one clause at a time.",
        next_lesson="ds2",
        order=1,
    ),
    Lesson(
        id="ds2",
        module="descriptive",
        level="Intermediate",
        title="Grouping, conditional logic and NULL handling",
        tools=["SQL"],
        minutes=40,
        competencies=["sql_aggregation", "kpi_reporting"],
        objectives=[
            "Aggregate by one or more dimensions with GROUP BY.",
            "Filter groups with HAVING and rows with WHERE - and know the difference.",
            "Create business categories with CASE expressions.",
            "Handle NULLs deliberately with COALESCE, IS NULL and NULLIF.",
        ],
        concept=f"""
`GROUP BY` collapses rows that share the same values into one row per group, and aggregates summarise each group.
Every selected column must be either **grouped** or **aggregated**.

* `WHERE` filters **rows before** grouping; `HAVING` filters **groups after** aggregation (`HAVING SUM(x) > 1000`).
* `CASE WHEN condition THEN value ... ELSE value END` turns raw values into business categories (price bands, discount tiers, size segments). Conditions are tested top to bottom; the first match wins.
* NULL means *unknown*, not zero. `NULL + 1` is NULL, `NULL = NULL` is not true, and `WHERE col = NULL` matches nothing - use `IS NULL`.
* `COALESCE(discount_pct, 0)` replaces NULL with 0 - but only do this when the business confirms that missing means zero, and document it.
* `NULLIF(denominator, 0)` avoids division-by-zero errors in ratios.
* Conditional aggregation computes several metrics in one pass: `SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END)` or DuckDB's `COUNT(*) FILTER (WHERE status='Cancelled')`.

{REVENUE_NOTE}
""",
        business_context="""
The commercial director wants to know whether discounting is "buying" revenue. A first step is to summarise lines and revenue by discount band, keeping lines with an *unknown* discount visible rather than silently treating them as full price.
""",
        worked_example=WorkedExample(
            language="sql",
            search_path="retail",
            code="""-- Cancellation rate and revenue by region (2024)
SELECT
    o.region,
    COUNT(*)                                                    AS orders,
    SUM(CASE WHEN o.status = 'Cancelled' THEN 1 ELSE 0 END)     AS cancelled,
    ROUND(100.0 * SUM(CASE WHEN o.status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                        AS cancel_rate_pct
FROM orders AS o
WHERE o.order_date >= DATE '2024-01-01' AND o.order_date < DATE '2025-01-01'
GROUP BY o.region
HAVING COUNT(*) > 100
ORDER BY cancel_rate_pct DESC;""",
            explanation="""
* Conditional aggregation (`SUM(CASE ...)`) counts cancelled orders inside each region group.
* `100.0 *` forces decimal division; integer division would round down to 0.
* `HAVING COUNT(*) > 100` drops tiny groups whose rates would be noisy - a common reporting rule.
* **Interpretation:** a region with a higher cancellation rate is a lead for investigation, not a conclusion. Check volumes and confidence before acting.
""",
        ),
        knowledge_check=["q_ds_004", "q_ds_005", "q_ds_006"],
        guided_exercise="ex_sql_ds2_discount_bands",
        challenge="ex_sql_ds2_loyal_customers",
        summary=[
            "Every selected column must be grouped or aggregated.",
            "WHERE filters rows; HAVING filters groups.",
            "CASE builds business categories; order the WHEN branches carefully.",
            "NULL is unknown: use IS NULL, COALESCE and NULLIF deliberately and document assumptions.",
        ],
        common_mistakes=[
            "Putting an aggregate condition in WHERE.",
            "Integer division producing 0% rates.",
            "Replacing NULLs with 0 without checking what NULL means.",
        ],
        revision="If HAVING vs WHERE is unclear, revisit the logical query order in lesson ds1.",
        next_lesson="ds3",
        order=2,
    ),
    Lesson(
        id="ds3",
        module="descriptive",
        level="Intermediate",
        title="Joins, CTEs and subqueries",
        tools=["SQL"],
        minutes=45,
        competencies=["sql_joins", "kpi_reporting"],
        objectives=[
            "Choose INNER, LEFT, RIGHT and FULL joins based on which rows must be kept.",
            "Predict the grain of a joined result and avoid double counting.",
            "Find unmatched records with anti-joins.",
            "Structure multi-step logic with common table expressions (CTEs) and subqueries.",
        ],
        concept="""
A join combines rows from two tables using a key.

| Join | Keeps |
|---|---|
| `INNER JOIN` | only rows with a match in both tables |
| `LEFT JOIN` | all rows of the left table; NULLs where the right has no match |
| `RIGHT JOIN` | all rows of the right table (rarely needed - swap table order and use LEFT) |
| `FULL JOIN` | all rows from both sides |

**Grain is everything.** Joining `orders` (one row per order) to `order_items` (one row per line) produces one row per *line*. If you then `SUM(o.shipping_cost)` you add each order's shipping fee once per line - a classic double count. Aggregate to the right grain *before* joining, or aggregate each measure at its own grain.

**Anti-join:** `LEFT JOIN ... WHERE right.key IS NULL` returns rows with no match (e.g. customers who never ordered). `NOT EXISTS (subquery)` is an equivalent, often clearer form.

**CTEs** (`WITH name AS (...)`) name intermediate results so a query reads top-to-bottom like a recipe. They make validation easy: run each CTE on its own and check row counts.

**Subqueries** can appear in `WHERE` (`customer_id IN (SELECT ...)`), in `FROM` (a derived table) or in `SELECT` (a scalar subquery).
""",
        business_context="""
Finance wants gross margin by category. Revenue lives in `order_items`, status in `orders`, cost in `products` and category names in `categories` - four tables, three joins. Marketing separately wants to know how many recently acquired customers have never bought anything, by channel.
""",
        worked_example=WorkedExample(
            language="sql",
            search_path="retail",
            code="""-- Revenue by department, built step by step with CTEs
WITH completed_lines AS (
    SELECT oi.product_id,
           oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0)) AS revenue
    FROM order_items AS oi
    JOIN orders      AS o  ON o.order_id = oi.order_id
    WHERE o.status = 'Completed'
),
by_product AS (
    SELECT product_id, SUM(revenue) AS revenue
    FROM completed_lines
    GROUP BY product_id
)
SELECT c.department,
       ROUND(SUM(bp.revenue), 2) AS revenue,
       COUNT(*)                  AS products_sold
FROM by_product AS bp
JOIN products   AS p ON p.product_id  = bp.product_id
JOIN categories AS c ON c.category_id = p.category_id
GROUP BY c.department
ORDER BY revenue DESC;""",
            explanation="""
1. `completed_lines` - grain: one row per completed order line, with revenue computed once.
2. `by_product` - aggregates to one row per product **before** joining dimensions, so nothing can be double counted.
3. The final SELECT attaches product -> category -> department and aggregates again.

**Check:** the total of `revenue` should equal total completed revenue from a simple query on `order_items` + `orders`. Reconciling totals is the fastest way to catch join errors.
""",
        ),
        extra_examples=[
            WorkedExample(
                language="sql",
                search_path="retail",
                code="""-- Anti-join: products that have never been ordered
SELECT p.product_id, p.product_name
FROM products AS p
WHERE NOT EXISTS (SELECT 1 FROM order_items AS oi WHERE oi.product_id = p.product_id);""",
                explanation="`NOT EXISTS` stops at the first match for each product and handles NULLs safely (unlike `NOT IN` with a NULL in the list).",
            )
        ],
        knowledge_check=["q_ds_007", "q_ds_008", "q_ds_009"],
        guided_exercise="ex_sql_ds3_category_margin",
        challenge="ex_sql_ds3_never_ordered",
        summary=[
            "Choose the join type by deciding which rows must survive.",
            "State the grain of every intermediate result; aggregate before joining when grains differ.",
            "Anti-joins (LEFT JOIN ... IS NULL / NOT EXISTS) find missing relationships.",
            "CTEs make multi-step queries readable and individually testable.",
        ],
        common_mistakes=[
            "Summing order-level values after joining to line-level tables.",
            "Filtering the right table of a LEFT JOIN in WHERE, which silently turns it into an INNER JOIN (put the condition in ON).",
            "Using NOT IN with a subquery that can return NULL.",
        ],
        revision="Draw the grain of each table before writing a join. Revisit ds2 if GROUP BY feels shaky.",
        next_lesson="ds4",
        order=3,
    ),
    Lesson(
        id="ds4",
        module="descriptive",
        level="Advanced",
        title="Window functions, rankings and period comparisons",
        tools=["SQL"],
        minutes=50,
        competencies=["sql_window", "kpi_reporting"],
        objectives=[
            "Explain how window functions differ from GROUP BY.",
            "Rank items within groups with ROW_NUMBER, RANK and DENSE_RANK.",
            "Compute running totals and moving averages with frame clauses.",
            "Compare periods with LAG/LEAD and date functions (DATE_TRUNC, EXTRACT).",
        ],
        concept="""
A **window function** computes a value for each row using a set of related rows (the *window*) **without collapsing** them:

```sql
function(...) OVER (PARTITION BY group_cols ORDER BY sort_cols ROWS BETWEEN ... )
```

* `PARTITION BY` restarts the calculation for each group (like GROUP BY, but rows are kept).
* `ORDER BY` inside OVER defines sequence for rankings, running totals and LAG/LEAD.
* Frame clauses control which rows are included: `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` gives a 3-period moving average.

| Need | Function |
|---|---|
| Unique sequence per group | `ROW_NUMBER()` |
| Rank with gaps after ties (1,1,3) | `RANK()` |
| Rank without gaps (1,1,2) | `DENSE_RANK()` |
| Previous / next period | `LAG(x)`, `LEAD(x)` |
| Running total | `SUM(x) OVER (ORDER BY month)` |
| Share of total | `x / SUM(x) OVER ()` |

Windows are evaluated **after** WHERE/GROUP BY, so you cannot filter on them in WHERE. Wrap the query in a CTE, or use DuckDB's `QUALIFY` clause (`QUALIFY rnk <= 3`).

**Date functions:** `DATE_TRUNC('month', order_date)` maps each date to the first day of its month; `EXTRACT(year FROM order_date)` or `YEAR(order_date)` pulls parts out; `order_date - INTERVAL 1 YEAR` shifts dates for year-over-year comparisons.
""",
        business_context="""
The monthly business review needs month-over-month growth, a year-to-date revenue line and the top products in each category. These are the most requested numbers in any retail reporting pack - and the most frequently miscalculated when done by hand in spreadsheets.
""",
        worked_example=WorkedExample(
            language="sql",
            search_path="retail",
            code="""WITH monthly AS (
    SELECT DATE_TRUNC('month', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0))) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY 1
)
SELECT month,
       ROUND(revenue, 0)                                           AS revenue,
       ROUND(LAG(revenue, 12) OVER (ORDER BY month), 0)            AS revenue_same_month_last_year,
       ROUND(100 * (revenue / LAG(revenue, 12) OVER (ORDER BY month) - 1), 1) AS yoy_growth_pct,
       ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0) AS moving_avg_3m
FROM monthly
ORDER BY month;""",
            explanation="""
* `monthly` aggregates to one row per month first; window functions then operate on those 24 rows.
* `LAG(revenue, 12)` looks 12 rows back = the same month last year (valid only because there is exactly one row per month and no gaps - always verify that assumption).
* The 3-month moving average smooths noise; note that the first two months average fewer than 3 values.
* **Interpretation:** year-over-year comparisons remove seasonality (December vs December), which month-over-month comparisons do not.
""",
        ),
        knowledge_check=["q_ds_010", "q_ds_011", "q_ds_012"],
        guided_exercise="ex_sql_ds4_mom_growth",
        challenge="ex_sql_ds4_top3_per_category",
        summary=[
            "Window functions keep rows; GROUP BY collapses them.",
            "PARTITION BY = per group, ORDER BY = sequence, frame = which rows.",
            "Use DENSE_RANK/RANK/ROW_NUMBER deliberately based on tie handling.",
            "Year-over-year growth controls for seasonality; LAG assumes no gaps in the series.",
        ],
        common_mistakes=[
            "Filtering a window result in WHERE (use a CTE or QUALIFY).",
            "Using LAG on a series with missing months.",
            "Forgetting PARTITION BY when computing running totals per year.",
        ],
        revision="Rebuild the worked example one column at a time. Review CTEs in ds3 if the structure is confusing.",
        next_lesson="ds5",
        order=4,
    ),
    Lesson(
        id="ds5",
        module="descriptive",
        level="Intermediate",
        title="Excel for analysts: formulas, lookups, PivotTables and what-if analysis",
        tools=["Excel", "Python"],
        minutes=45,
        competencies=["excel_analysis", "kpi_reporting"],
        objectives=[
            "Use relative, absolute and mixed references correctly.",
            "Apply IF/IFS, SUMIFS/COUNTIFS and XLOOKUP to business questions.",
            "Summarise data with PivotTables and explain the equivalent SQL/pandas logic.",
            "Build a what-if scenario table and an auditable workbook layout.",
        ],
        concept="""
**References.** `A1` is relative (shifts when copied), `$A$1` is absolute (never shifts), `$A1`/`A$1` are mixed. Put assumptions (tax rate, target margin) in labelled input cells and reference them absolutely: `=B2*$H$1`.

**Logic and conditional aggregation**

| Formula | Purpose | SQL equivalent |
|---|---|---|
| `=IF(C2>100,"High","Low")` | binary rule | `CASE WHEN ... END` |
| `=IFS(C2>=500,"A",C2>=100,"B",TRUE,"C")` | multiple rules | `CASE` with several WHENs |
| `=SUMIFS(Rev, Region,"West", Year,2024)` | conditional sum | `SUM(...) WHERE ... GROUP BY` |
| `=COUNTIFS(Status,"Cancelled")` | conditional count | `COUNT(*) FILTER (WHERE ...)` |
| `=XLOOKUP(id, Products[id], Products[price], "not found")` | lookup | `LEFT JOIN` |

`XLOOKUP` replaces `VLOOKUP` (which breaks when columns are inserted and defaults to approximate matching). In older Excel use `INDEX(return_range, MATCH(key, lookup_range, 0))`.

**Text and dates:** `TEXT`, `LEFT`, `TRIM`, `PROPER`, `DATE`, `EOMONTH`, `YEAR`, `NETWORKDAYS`.

**Tables & PivotTables.** Convert data to an Excel Table (Ctrl+T) so formulas use structured references and ranges grow automatically. A PivotTable is a GROUP BY with a drag-and-drop interface: *Rows* and *Columns* are grouping dimensions, *Values* are aggregates, *Filters/Slicers* are WHERE clauses.

**What-if analysis.** *Data -> What-If Analysis -> Data Table* recalculates an output (e.g. profit) for a grid of input values (price x volume). *Goal Seek* finds the input that achieves a target.

**Auditability.** Separate *Inputs*, *Calculations* and *Outputs* sheets; colour input cells consistently; avoid hard-coded numbers inside formulas; add a *Checks* area (e.g. totals reconcile to source).
""",
        business_context="""
Regional managers live in Excel. They need a revenue PivotTable by region and segment and a simple model showing how profit responds to price changes. Your job is to make the workbook correct **and** auditable so another analyst can verify it.
""",
        worked_example=WorkedExample(
            language="excel",
            runnable=False,
            code="""Sheet "Inputs":     H1 = target margin (0.35)       H2 = price change (0.05)
Sheet "Data" (Table named Sales): OrderDate | Region | Segment | Revenue | Cost

Revenue West 2024    =SUMIFS(Sales[Revenue], Sales[Region], "West", Sales[OrderDate], ">="&DATE(2024,1,1), Sales[OrderDate], "<"&DATE(2025,1,1))
Margin %             =IFERROR((Revenue - Cost) / Revenue, 0)
Meets target?        =IF(MarginPct >= Inputs!$H$1, "Yes", "No")
Category name        =XLOOKUP([@ProductID], Products[ProductID], Products[Category], "Unknown")
Scenario revenue     =[@Revenue] * (1 + Inputs!$H$2)""",
            explanation="""
* Criteria pairs in `SUMIFS` are combined with AND; date criteria are built with `">="&DATE(...)`.
* `Inputs!$H$1` is absolute so every row uses the same target.
* `IFERROR` protects against division by zero but can also hide genuine errors - use it sparingly and only where you know which error you expect.
* The same logic in pandas is shown below; running it gives the numbers your workbook should reproduce.
""",
        ),
        extra_examples=[
            WorkedExample(
                language="python",
                preload={"orders": "retail.orders", "items": "retail.order_items", "customers": "retail.customers"},
                code="""# PivotTable equivalent: revenue by region (rows) x segment (columns), completed 2024 orders
df = items.merge(orders, on="order_id").merge(customers[["customer_id", "segment"]], on="customer_id")
df = df[(df.status == "Completed") & (df.order_date.dt.year == 2024)]
df["revenue"] = df.quantity * df.unit_price * (1 - df.discount_pct.fillna(0))
pivot = pd.pivot_table(df, index="region", columns="segment", values="revenue", aggfunc="sum", margins=True, margins_name="Total")
print(pivot.round(0))""",
                explanation="`pd.pivot_table` mirrors an Excel PivotTable: `index` = Rows, `columns` = Columns, `values`+`aggfunc` = Values, `margins` = Grand totals.",
            )
        ],
        knowledge_check=["q_ds_013", "q_ds_014", "q_ds_015"],
        guided_exercise="ex_py_ds5_pivot",
        challenge=None,
        tool_workshop="excel_workbook",
        summary=[
            "Absolute references anchor assumptions; keep inputs in labelled cells.",
            "SUMIFS/COUNTIFS are conditional GROUP BYs; XLOOKUP is a safe lookup (LEFT JOIN).",
            "PivotTables = GROUP BY with Rows/Columns/Values/Filters.",
            "Separate inputs, calculations, outputs and checks so others can audit your workbook.",
        ],
        common_mistakes=[
            "VLOOKUP with approximate match (the default) returning wrong values silently.",
            "Hard-coding numbers inside formulas instead of referencing input cells.",
            "PivotTables built on a fixed range that does not grow with new data.",
        ],
        revision="Complete the Excel Workbook workshop and compare your SUMIFS results with the pandas output.",
        next_lesson="ds6",
        order=5,
    ),
    Lesson(
        id="ds6",
        module="descriptive",
        level="Advanced",
        title="Power BI: star schemas, relationships and DAX measures",
        tools=["Power BI", "SQL"],
        minutes=50,
        competencies=["bi_modeling", "kpi_reporting"],
        objectives=[
            "Design a star schema with fact and dimension tables.",
            "Configure relationships (cardinality, filter direction) correctly.",
            "Write basic DAX measures for revenue, margin, growth and YTD.",
            "Explain filter context, slicers, drill-down and cross-filtering.",
        ],
        concept="""
**Power Query** (Get Data -> Transform) is where you clean and shape data: change types, remove columns, merge and append queries. Every step is recorded and replayed on refresh - the same reproducibility principle as a script.

**Star schema.** A central **fact** table holds events and numeric measures at a defined grain (`order_items`: one row per order line). **Dimension** tables describe the facts (`products`, `customers`, `calendar`). Relationships run *one* (dimension) -> *many* (fact), with filters flowing from dimensions to facts.

* Prefer single-direction filtering; bi-directional filters create ambiguity and slow models.
* Always add a dedicated **Date/Calendar table** (marked as a date table) for time intelligence.
* Snowflaked dimensions (product -> category) work but flattening them into one product dimension is usually simpler.

**Measures vs calculated columns.** A *calculated column* is computed row by row at refresh and stored (use for slicing/grouping, e.g. price band). A *measure* is computed at query time in the current **filter context** (use for aggregates such as revenue). Most KPIs should be measures.

```DAX
Revenue      = SUMX(order_items, order_items[quantity] * order_items[unit_price] * (1 - order_items[discount_pct]))
Cost         = SUMX(order_items, order_items[quantity] * RELATED(products[unit_cost]))
Margin %     = DIVIDE([Revenue] - [Cost], [Revenue])
Revenue YTD  = TOTALYTD([Revenue], 'Calendar'[Date])
Revenue PY   = CALCULATE([Revenue], SAMEPERIODLASTYEAR('Calendar'[Date]))
YoY %        = DIVIDE([Revenue] - [Revenue PY], [Revenue PY])
```

**Filter context** is the set of filters (slicers, visual axes, page filters) applied when a measure is evaluated. `CALCULATE` modifies filter context; `DIVIDE` handles division by zero.

**Interaction:** slicers filter the page; selecting a bar *cross-filters* other visuals; drill-down moves from year -> quarter -> month in a hierarchy.

**Refresh & performance:** import mode is fastest; remove unused columns, avoid high-cardinality text columns in facts, and prefer measures over calculated columns.
""",
        business_context="""
Northwind wants a Power BI sales dashboard. Before building visuals you must design the model: which table is the fact, which are dimensions, how they relate, and which measures the dashboard needs. A wrong relationship produces numbers that *look* plausible but are wrong in every visual.
""",
        worked_example=WorkedExample(
            language="sql",
            search_path="retail",
            code="""-- What Power BI's [Revenue YTD] measure would show, reproduced in SQL for validation
WITH monthly AS (
    SELECT YEAR(o.order_date) AS year, MONTH(o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0))) AS revenue
    FROM orders o JOIN order_items oi USING (order_id)
    WHERE o.status = 'Completed'
    GROUP BY ALL
)
SELECT year, month, ROUND(revenue, 0) AS revenue,
       ROUND(SUM(revenue) OVER (PARTITION BY year ORDER BY month), 0) AS revenue_ytd
FROM monthly ORDER BY year, month;""",
            explanation="""
`TOTALYTD` restarts each year - the SQL equivalent is a running SUM with `PARTITION BY year`.
Professional BI developers reconcile key measures against an independent query like this before publishing a dashboard.
""",
        ),
        knowledge_check=["q_ds_016", "q_ds_017", "q_ds_018"],
        guided_exercise="ex_sql_ds6_ytd",
        challenge=None,
        tool_workshop="powerbi_model",
        summary=[
            "Facts hold measurable events at a defined grain; dimensions describe them.",
            "One-to-many, single-direction relationships from dimension to fact are the default.",
            "Measures respond to filter context; calculated columns are static per row.",
            "Validate dashboard measures against an independent SQL or pandas calculation.",
        ],
        common_mistakes=[
            "Using implicit sums of columns instead of explicit measures.",
            "Bi-directional relationships everywhere 'to make it work'.",
            "No calendar table, so time-intelligence functions behave unexpectedly.",
        ],
        revision="Do the Power BI Model Designer workshop and the DAX measure check.",
        next_lesson="ds7",
        order=6,
    ),
    Lesson(
        id="ds7",
        module="descriptive",
        level="Professional",
        title="KPI design and business reporting",
        tools=["SQL", "Excel", "Power BI"],
        minutes=45,
        competencies=["kpi_reporting", "sql_joins", "sql_aggregation"],
        objectives=[
            "Define KPIs precisely (formula, filters, grain, owner, target).",
            "Distinguish metrics, dimensions, assumptions and constraints.",
            "Build a monthly KPI report and reconcile it.",
            "Explain the business implications of KPI movements, not just the numbers.",
        ],
        concept="""
A KPI is only useful if everybody computes it the same way. Write a **KPI definition card** for each:

| Field | Example: Average Order Value (AOV) |
|---|---|
| Business question | How much does a typical order earn us? |
| Formula | completed revenue / number of completed orders |
| Filters | status = Completed; excludes shipping fees |
| Grain & period | monthly, by region |
| Owner | E-commerce manager |
| Target / threshold | >= EUR 165 |
| Caveats | sensitive to bulk orders; review median too |

**Metrics vs dimensions.** Metrics are numbers you aggregate (revenue, orders). Dimensions are attributes you slice by (region, month). **Assumptions** are choices you made (NULL discount = 0). **Constraints** limit what is possible (data only from 2023).

**Good KPI sets** combine *outcome* metrics (revenue, margin) with *driver* metrics (orders, AOV, conversion, return rate) so a change can be explained: Revenue = Orders x AOV.

**Ratios need care:** compute ratios from summed components (`SUM(revenue) / SUM(orders)`), never by averaging pre-computed ratios.

**Reporting discipline:** reconcile totals with the source, show comparison periods, annotate known events, and lead with the "so what".

**Query readability & performance:** use CTEs with meaningful names, one column per line, consistent aliases; filter early, select only needed columns, and avoid functions on filter columns where possible (they can prevent index/zone-map pruning).
""",
        business_context="""
The CEO wants a one-page monthly KPI report for 2024: orders, revenue, AOV and gross margin %, plus a view of returns by category. You must produce the numbers **and** say what they mean for the business.
""",
        worked_example=WorkedExample(
            language="sql",
            search_path="retail",
            code="""-- Revenue decomposition: Revenue = Orders x AOV, by quarter
WITH lines AS (
    SELECT o.order_id, DATE_TRUNC('quarter', o.order_date) AS quarter,
           oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0)) AS revenue
    FROM orders o JOIN order_items oi USING (order_id)
    WHERE o.status = 'Completed'
)
SELECT quarter,
       COUNT(DISTINCT order_id)                          AS orders,
       ROUND(SUM(revenue), 0)                            AS revenue,
       ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2) AS aov
FROM lines
GROUP BY quarter
ORDER BY quarter;""",
            explanation="""
* AOV is computed from **summed components**, not by averaging order values per region and then averaging again.
* If revenue grows, the decomposition tells you whether it came from more orders, larger orders, or both - this is the start of a diagnostic story.
* Always mention the definition (completed orders, excludes shipping) next to the number.
""",
        ),
        knowledge_check=["q_ds_019", "q_ds_020", "q_ds_021", "q_ds_022"],
        guided_exercise="ex_sql_ds7_monthly_kpis",
        challenge="ex_sql_ds7_return_rates",
        summary=[
            "Define each KPI with formula, filters, grain, owner, target and caveats.",
            "Pair outcome metrics with driver metrics so movements can be explained.",
            "Compute ratios from summed components.",
            "Lead reports with implications and reconcile numbers to the source.",
        ],
        common_mistakes=[
            "Averaging averages.",
            "KPIs with no stated filters, so different teams get different numbers.",
            "Reporting numbers without comparisons or context.",
        ],
        revision="Write KPI definition cards for revenue, AOV and return rate, then start Capstone 1.",
        next_lesson="dg1",
        order=7,
    ),
]
