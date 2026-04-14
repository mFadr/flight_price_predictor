"""Module 5 - Data Visualization & Communication (Matplotlib, Tableau, Looker Studio, Power BI, Excel)."""

from analytics_lab.models import Lesson, WorkedExample

LESSONS = [
    Lesson(
        id="vz1",
        module="visualization",
        level="Beginner",
        title="Choosing the right chart for the question",
        tools=["Matplotlib", "Excel", "Power BI"],
        minutes=35,
        competencies=["chart_selection"],
        objectives=[
            "Map analytical questions (comparison, trend, distribution, relationship, composition) to chart types.",
            "Know when a table beats a chart.",
            "Distinguish univariate, bivariate and multivariate views.",
            "Choose charts for the audience and the decision.",
        ],
        concept="""
Start from the **question**, not the chart gallery.

| Question type | Good choices | Avoid |
|---|---|---|
| Compare categories | sorted bar chart (horizontal for long labels), dot plot | pie with many slices, 3-D bars |
| Trend over time | line chart; column chart for few periods | unordered bars, pie |
| Distribution (one variable) | histogram, box plot, violin, ECDF | bar of means only |
| Relationship (two numeric) | scatter plot (+ trend line), hexbin for many points | dual-axis line charts implying correlation |
| Composition | stacked bar (few parts), 100% stacked bar, treemap | pie with > 4-5 slices |
| Geography | choropleth map (rates, not totals), symbol map | maps when location is not the point |
| Exact lookup | table with conditional formatting | chart |
| Many variables | small multiples, heatmap, scatter matrix | one overloaded chart |

**Univariate** views describe one variable (histogram). **Bivariate** views relate two (scatter, grouped box plot). **Multivariate** views add a third via colour, size or facets (small multiples are usually clearer than bubble charts).

**Audience and decision:** executives need the answer and its implication (one clear chart, annotated); analysts need exploration (interactive filters, detail). A chart that answers "which region is under target?" should make the target and the gap obvious.

**Excel and Power BI** offer the same core visuals: clustered bar/column, line, scatter, histogram, box and whisker (Excel 2016+), map, matrix, KPI card. The selection rules are identical across tools.
""",
        business_context="""
Northwind's leadership asks four questions: Which categories earn the most? Is revenue growing? Are order values typically small or large? Do bigger discounts produce bigger orders? Each needs a different chart.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"items": "retail.order_items", "orders": "retail.orders"},
            code="""df = items.merge(orders, on="order_id").query("status == 'Completed'")
df["revenue"] = df.quantity * df.unit_price * (1 - df.discount_pct.fillna(0))
order_value = df.groupby("order_id").revenue.sum()
monthly = df.groupby(df.order_date.dt.to_period("M")).revenue.sum()

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].plot(monthly.index.to_timestamp(), monthly.values / 1e3, color="#2563eb")
axes[0].set(title="Trend: monthly revenue", ylabel="Revenue (EUR k)")
axes[0].set_ylim(bottom=0)

axes[1].hist(order_value.clip(upper=2000), bins=40, color="#64748b")
axes[1].set(title="Distribution: order value (capped at 2,000)", xlabel="Order value (EUR)", ylabel="Orders")

sample = df.sample(3000, random_state=0)
axes[2].scatter(sample.discount_pct.fillna(0) * 100, sample.revenue, s=6, alpha=0.3, color="#0f766e")
axes[2].set(title="Relationship: discount vs line revenue", xlabel="Discount (%)", ylabel="Line revenue (EUR)", yscale="log")
fig.tight_layout()""",
            explanation="""
* **Trend** -> line chart with a zero baseline for an amount.
* **Distribution** -> histogram; capping at 2,000 keeps the shape visible (state the cap in the title).
* **Relationship** -> scatter; a log scale handles the skew, and transparency (`alpha`) handles over-plotting.
""",
        ),
        knowledge_check=["q_vz_001", "q_vz_002", "q_vz_003"],
        guided_exercise="ex_py_vz1_bar",
        challenge=None,
        summary=[
            "Pick the chart from the question type: comparison, trend, distribution, relationship, composition.",
            "Tables are better for precise lookups.",
            "Use small multiples for many variables.",
            "Design for the audience and the decision.",
        ],
        common_mistakes=[
            "Pie charts with many slices.",
            "Unsorted bar charts.",
            "Showing only averages when the distribution matters.",
        ],
        revision="For each of the five dataset 'suggested questions', name the best chart and why.",
        next_lesson="vz2",
        order=26,
    ),
    Lesson(
        id="vz2",
        module="visualization",
        level="Intermediate",
        title="Matplotlib fundamentals: axes, scales, labels and annotations",
        tools=["Matplotlib"],
        minutes=45,
        competencies=["viz_coding"],
        objectives=[
            "Use the object-oriented Matplotlib API (fig, ax).",
            "Set titles, axis labels with units, ticks, limits and scales.",
            "Annotate key events and values directly on the chart.",
            "Build small multiples with subplots.",
        ],
        concept="""
Matplotlib has two interfaces; prefer the **object-oriented** one for anything beyond a quick look:

```python
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(x, y, color="#2563eb", linewidth=2, label="Revenue")
ax.set_title("Monthly revenue, 2023-2024")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (EUR thousands)")
ax.set_ylim(bottom=0)
ax.annotate("Holiday peak", xy=(x_peak, y_peak), xytext=(x_peak, y_peak * 1.1),
            arrowprops=dict(arrowstyle="->"), ha="center")
ax.legend(frameon=False)
fig.tight_layout()
```

**Essentials checklist**

* **Title** that states the point ("Revenue peaks every December") or at least the subject and period.
* **Axis labels with units** (EUR, %, thousands). Format ticks: `ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))` or `FuncFormatter`.
* **Scales:** bars must start at zero; lines may zoom when the *change* matters, but say so. Use log scales for multiplicative data and label them.
* **Annotations** explain events (promotions, stock-outs) where the eye already is - better than a legend or footnote.
* **Legends:** use only when needed; direct labels at line ends are easier to read.
* **Small multiples:** `fig, axes = plt.subplots(2, 3, sharex=True, sharey=True)` - shared axes make panels comparable.
* **Remove clutter:** `ax.spines[["top", "right"]].set_visible(False)`; light grid lines or none.

In the lab, figures you create are captured and displayed automatically - no `plt.show()` needed (it is harmless).
""",
        business_context="""
The monthly review deck needs a revenue trend chart that a non-technical audience can read in five seconds, with the West stock-out explicitly annotated so nobody misreads the dip.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"items": "retail.order_items", "orders": "retail.orders"},
            code="""import matplotlib.ticker as mtick

df = items.merge(orders, on="order_id").query("status == 'Completed' and region == 'West'")
df["revenue"] = df.quantity * df.unit_price * (1 - df.discount_pct.fillna(0))
m = df.groupby(df.order_date.dt.to_period("M")).revenue.sum()
x, y = m.index.to_timestamp(), m.values

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(x, y, color="#2563eb", linewidth=2)
ax.set_title("West region revenue dipped in Aug-Sep 2024, then recovered")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (EUR)")
ax.set_ylim(bottom=0)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v / 1e3:.0f}k"))
ax.axvspan(pd.Timestamp("2024-08-01"), pd.Timestamp("2024-09-30"), color="#f59e0b", alpha=0.15)
low = m.loc["2024-08":"2024-09"].idxmin().to_timestamp()
ax.annotate("Electronics stock-out", xy=(low, m.loc["2024-08":"2024-09"].min()),
            xytext=(pd.Timestamp("2024-03-01"), y.max() * 0.35), arrowprops=dict(arrowstyle="->"))
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()""",
            explanation="""
* The title states the finding; the shaded span and annotation explain the dip in place.
* `set_ylim(bottom=0)` keeps the size of the dip honest; the formatter makes ticks readable (90k instead of 90000).
* Removing the top and right spines reduces clutter without losing information.
""",
        ),
        knowledge_check=["q_vz_004", "q_vz_005", "q_vz_006"],
        guided_exercise="ex_py_vz2_line",
        challenge=None,
        summary=[
            "Use fig, ax = plt.subplots() and set everything explicitly.",
            "Titles state the point; labels carry units.",
            "Annotate events directly on the chart.",
            "Small multiples with shared axes enable comparison.",
        ],
        common_mistakes=[
            "Missing units on axes.",
            "Legends that force the reader to look back and forth.",
            "Inconsistent axes across small multiples.",
        ],
        revision="Turn the worked example into small multiples: one panel per region with shared y-axes.",
        next_lesson="vz3",
        order=27,
    ),
    Lesson(
        id="vz3",
        module="visualization",
        level="Intermediate",
        title="Design principles: colour, hierarchy, accessibility and clutter",
        tools=["Matplotlib", "Tableau", "Power BI"],
        minutes=40,
        competencies=["viz_integrity", "viz_coding"],
        objectives=[
            "Use colour purposefully: categorical, sequential, diverging, highlight.",
            "Create visual hierarchy with size, weight, position and whitespace.",
            "Design for colour-vision deficiencies and sufficient contrast.",
            "Remove clutter to reduce cognitive load.",
        ],
        concept="""
**Colour has three jobs:**

* *Categorical* - distinguish groups (max ~6-8 distinct hues).
* *Sequential* - ordered magnitude (light -> dark of one hue), e.g. churn rate on a map.
* *Diverging* - deviation from a meaningful midpoint (below/above target), two hues with a neutral middle.
* *Highlight* - grey everything, colour the one thing that matters. Often the most effective choice in business charts.

**Accessibility**

* ~8% of men have a colour-vision deficiency; red/green distinctions are the most common problem. Use colour-blind-safe palettes (e.g. Okabe-Ito, viridis) and redundant encoding (labels, shapes, position).
* Text contrast >= 4.5:1 against its background (WCAG AA). Avoid light grey text on white.
* Do not rely on colour alone to carry meaning; add direct labels.
* Provide alt text or a one-sentence takeaway for screen readers.

**Hierarchy and whitespace.** The most important element should be the most prominent (position top-left, larger, bolder, coloured). Align elements on a grid; group related items; leave whitespace between groups.

**Clutter and cognitive load (data-ink ratio).** Remove what does not inform: heavy borders, background fills, 3-D effects, redundant legends, excessive gridlines, decimal places nobody needs. Every element should earn its place.

**Typography:** one font family, two or three sizes, sentence case, horizontal text (rotate the chart - use horizontal bars - rather than the labels).
""",
        business_context="""
The retention team's slide shows churn by acquisition source in five bright colours with a legend. Executives keep asking "which one is the problem?" Redesign it so the answer is obvious and accessible.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"cf": "subscription.churn_features"},
            code="""rates = cf.groupby("acquisition_source").churned_6m.mean().sort_values()
colors = ["#b0b7c3"] * len(rates)
colors[list(rates.index).index("Paid Social")] = "#d55e00"   # Okabe-Ito vermillion

fig, ax = plt.subplots(figsize=(8, 3.6))
bars = ax.barh(rates.index, rates.values * 100, color=colors)
ax.bar_label(bars, labels=[f"{v:.0%}" for v in rates.values], padding=3)
ax.set_title("Paid Social customers churn about twice as often as other sources", loc="left")
ax.set_xlabel("6-month churn rate (%)")
ax.set_xlim(0, rates.max() * 115)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(left=False)
fig.tight_layout()""",
            explanation="""
* **Highlight colour** directs attention; grey de-emphasises the context categories.
* Direct value labels replace the legend and make the chart readable without colour.
* Horizontal bars keep category labels horizontal; sorting puts the comparison in order.
* The title states the takeaway, so the chart works even if it is skimmed.
""",
        ),
        knowledge_check=["q_vz_007", "q_vz_008", "q_vz_009"],
        guided_exercise="ex_py_vz3_highlight",
        challenge=None,
        summary=[
            "Choose categorical, sequential, diverging or highlight colour deliberately.",
            "Design for colour-vision deficiency and contrast; never rely on colour alone.",
            "Build hierarchy with position, size and whitespace.",
            "Remove non-informative ink.",
        ],
        common_mistakes=[
            "Rainbow palettes for ordered data.",
            "Red/green as the only distinction.",
            "Legends where direct labels would work.",
        ],
        revision="Recreate the chart with a sequential palette and explain why highlight works better here.",
        next_lesson="vz4",
        order=28,
    ),
    Lesson(
        id="vz4",
        module="visualization",
        level="Advanced",
        title="Misleading visualizations and how to fix them",
        tools=["Matplotlib", "Excel", "Power BI"],
        minutes=45,
        competencies=["viz_integrity", "chart_selection"],
        objectives=[
            "Recognise common misleading techniques.",
            "Critique a chart with specific, actionable improvements.",
            "Fix truncated axes, distorted areas and cherry-picked ranges in code.",
        ],
        concept="""
Charts mislead through design as much as through data. Common problems:

| Problem | Why it misleads | Fix |
|---|---|---|
| Truncated bar axis | bar length no longer proportional to value; small differences look huge | start bars at zero, or use dots/lines and state the zoom |
| Dual axes with arbitrary scales | the crossing point and slopes are artefacts of scaling | two aligned panels, or index both series to 100 |
| Cherry-picked time window | trend reverses outside the window | show the full relevant period or justify the window |
| 3-D effects / area & volume icons | perspective distorts size; area grows with the square of the radius | flat 2-D marks scaled by length |
| Inconsistent or reversed scales | readers assume up = more and equal intervals | conventional, consistent scales |
| Cumulative charts hiding declines | cumulative totals always rise | show period values |
| Totals on maps | big regions/populations dominate | normalise to rates per capita |
| Missing uncertainty | small samples look as precise as large ones | error bars, intervals, sample sizes |
| Pies with many slices / not summing to 100% | angles are hard to compare | sorted bars |

**A structured critique** names the problem, explains its effect on interpretation, and proposes a concrete fix: *"The y-axis starts at 9.5%, so treatment's 0.6 pp lift looks like a 3x difference. Start at 0% and add CIs, which also reveal that the difference is not significant."*

Misleading charts are often accidental (software defaults), but the analyst is responsible for the impression a chart creates.
""",
        business_context="""
A product manager's slide celebrates the checkout test with a bar chart whose y-axis starts at 9.8%. The CFO is about to approve rollout. Your job: critique the chart and produce an honest version.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"ab": "marketing.ab_test"},
            code="""rates = ab.groupby("variant").converted.mean() * 100
fig, (bad, good) = plt.subplots(1, 2, figsize=(11, 4))

bad.bar(rates.index, rates.values, color=["#94a3b8", "#16a34a"])
bad.set_ylim(9.8, 10.9)
bad.set_title("MISLEADING: axis starts at 9.8%")

n = ab.groupby("variant").size()
se = np.sqrt(rates / 100 * (1 - rates / 100) / n) * 100
good.bar(rates.index, rates.values, yerr=1.96 * se, capsize=6, color=["#94a3b8", "#2563eb"])
good.set_ylim(0, 13)
good.set_ylabel("Conversion rate (%)")
good.set_title("Honest: zero baseline with 95% CIs - overlap suggests no clear winner")
for i, v in enumerate(rates.values):
    good.text(i, v + 1.2, f"{v:.1f}%", ha="center")
fig.tight_layout()""",
            explanation="""
* On the left, a 0.6 percentage-point difference looks like treatment is several times better.
* On the right, the zero baseline shows the true proportion, and confidence intervals show the uncertainty - the visual now matches the statistical conclusion from lesson dg5.
""",
        ),
        knowledge_check=["q_vz_010", "q_vz_011", "q_vz_012"],
        guided_exercise="ex_py_vz4_fix",
        challenge=None,
        tool_workshop="chart_critique",
        summary=[
            "Bars start at zero; zoomed axes need explicit justification.",
            "Avoid dual axes, 3-D and area distortions; normalise maps.",
            "Show uncertainty and sample sizes.",
            "Critique = problem + effect on interpretation + concrete fix.",
        ],
        common_mistakes=[
            "Accepting software default axis ranges.",
            "Dual-axis charts suggesting correlations.",
            "Presenting tiny differences without uncertainty.",
        ],
        revision="Complete the Chart Critique workshop and explain each flaw in one sentence.",
        next_lesson="vz5",
        order=29,
    ),
    Lesson(
        id="vz5",
        module="visualization",
        level="Professional",
        title="Dashboards, data storytelling and communicating uncertainty",
        tools=["Matplotlib", "Power BI", "Tableau", "Looker Studio"],
        minutes=50,
        competencies=["storytelling", "viz_integrity"],
        objectives=[
            "Design dashboards around decisions and users.",
            "Lay out KPIs, trends and drill-downs with interactive filters.",
            "Write executive summaries and structure a data story.",
            "Visualise uncertainty with intervals and ranges.",
        ],
        concept="""
**Dashboards** support recurring decisions; **stories** support a one-off decision. Both start with: *who uses it, for which decision, how often?*

**Dashboard layout (top-left to bottom-right):**

1. **KPI cards** - current value, comparison (vs target / last year), trend sparkline.
2. **Trend** - main KPI over time with target line.
3. **Breakdown** - by the dimensions people act on (region, category).
4. **Detail** - table for drill-down.

Interactive **filters** (date, region) belong at the top or left; **drill-down** (year -> month) and **cross-filtering** (click a bar to filter others) let users explore without extra pages. Limit each view to 5-9 visuals; use consistent colours (one colour = one meaning across the whole dashboard).

**Data storytelling** - a classic structure:

1. **Context** - what the audience already knows and cares about.
2. **Complication** - what changed or what is at stake.
3. **Resolution** - your finding and recommendation.

Write the **executive summary first**: three to five sentences with the answer, the evidence and the ask. Each chart's title is a sentence that advances the story.

**Uncertainty** - always show it when decisions depend on it:

* error bars or interval bands (`ax.fill_between`) for estimates and forecasts;
* sample sizes next to rates;
* scenario ranges (low/base/high) for projections;
* words that match the evidence ("likely", "range of").

**Tool notes:** Power BI and Tableau dashboards support tooltips, drill-through and bookmarks; Looker Studio supports controls (date range, drop-down filters) and blended data sources. Principles are identical across tools.
""",
        business_context="""
The CEO wants a one-page overview: is the business healthy, where are the problems, what are we doing about them? You need a dashboard specification and a short story for the board.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"ab": "marketing.ab_test"},
            code="""g = ab.groupby(["device", "variant"]).converted.agg(["mean", "count"]).reset_index()
g["se"] = np.sqrt(g["mean"] * (1 - g["mean"]) / g["count"])
g["lo"], g["hi"] = g["mean"] - 1.96 * g["se"], g["mean"] + 1.96 * g["se"]

fig, ax = plt.subplots(figsize=(8, 4))
devices = ["desktop", "mobile", "tablet"]
for j, (variant, color) in enumerate([("control", "#94a3b8"), ("treatment", "#2563eb")]):
    sub = g[g.variant == variant].set_index("device").loc[devices]
    x = np.arange(len(devices)) + (j - 0.5) * 0.25
    ax.errorbar(x, sub["mean"] * 100, yerr=1.96 * sub["se"] * 100, fmt="o", capsize=5, color=color, label=variant)
    for xi, n in zip(x, sub["count"]):
        ax.text(xi, 2, f"n={n:,}", ha="center", fontsize=8, color="#475569")
ax.set_xticks(range(len(devices)), devices)
ax.set_ylim(0, 16)
ax.set_ylabel("Conversion rate (%) with 95% CI")
ax.set_title("Tablet estimates are too uncertain to act on; desktop and mobile overlap")
ax.legend(frameon=False)
fig.tight_layout()""",
            explanation="""
* Dots with intervals show estimates **and** their precision; the small tablet sample produces wide intervals.
* Sample sizes are printed so readers can judge reliability.
* The title tells the audience what conclusion is (and is not) supported.
""",
        ),
        knowledge_check=["q_vz_013", "q_vz_014", "q_vz_015"],
        guided_exercise="ex_py_vz5_uncertainty",
        challenge=None,
        summary=[
            "Design dashboards around users and decisions: KPIs -> trend -> breakdown -> detail.",
            "Stories follow context -> complication -> resolution; write the summary first.",
            "Show uncertainty with intervals, ranges and sample sizes.",
            "Keep colour meanings consistent across a dashboard.",
        ],
        common_mistakes=[
            "Dashboards that show everything and answer nothing.",
            "Chart titles that only name the metric.",
            "Point estimates without uncertainty for decisions that depend on it.",
        ],
        revision="Write a 4-sentence executive summary of the churn investigation, then start Capstone 5.",
        next_lesson="vz6",
        order=30,
    ),
    Lesson(
        id="vz6",
        module="visualization",
        level="Intermediate",
        title="Tableau workflow: data, fields, calculations and dashboards",
        tools=["Tableau"],
        minutes=45,
        competencies=["storytelling", "chart_selection"],
        objectives=[
            "Connect Tableau to CSV data and define relationships.",
            "Distinguish dimensions/measures and discrete/continuous fields.",
            "Write calculated fields, including LOD expressions.",
            "Assemble an interactive dashboard with filters and actions.",
        ],
        concept="""
> This lesson is a **guided assignment** for Tableau Desktop or Tableau Public (free). The lab cannot run Tableau itself; it provides the data, the tasks, the expected numbers to verify your work, and a self-check rubric.

**Data connection.** *Connect -> Text file* and pick `orders.csv`. Drag `order_items.csv`, `products.csv`, `categories.csv` and `customers.csv` onto the canvas to create **relationships** (Tableau's logical layer keeps each table at its own grain, which avoids the double counting that physical joins can cause).

**Field roles.** *Dimensions* (blue when discrete) slice data; *measures* (green when continuous) are aggregated. Discrete fields create headers; continuous fields create axes. Dates can be discrete (MONTH as a header) or continuous (a timeline).

**Calculated fields** (Analysis -> Create Calculated Field):

```
Revenue        = [Quantity] * [Unit Price (Order Items)] * (1 - ZN([Discount Pct]))
Completed Rev  = IF [Status] = "Completed" THEN [Revenue] END
Margin %       = (SUM([Completed Rev]) - SUM([Line Cost])) / SUM([Completed Rev])
Customer First Order = { FIXED [Customer Id] : MIN([Order Date]) }      // LOD expression
```

`ZN()` turns NULL into zero (state the assumption). **LOD expressions** compute values at a specified grain independent of the view - e.g. first order date per customer for cohort analysis.

**Building views:** drag fields to *Rows/Columns* shelves; use the *Marks* card for colour, size, label and tooltip; *Show Me* suggests chart types (apply the selection rules from lesson vz1).

**Dashboards:** combine sheets; add *filters* (apply to all worksheets using the same data source), *filter actions* (click a bar to filter other views), *highlight actions* and *parameters* (user-controlled inputs, e.g. target margin). Use a fixed size (e.g. 1200 x 800) and a clear layout grid.
""",
        business_context="""
Northwind's regional managers use Tableau Server. Build the "Retail Performance" workbook: revenue trend, category margin and regional drill-down with interactive filters.
""",
        worked_example=WorkedExample(
            language="text",
            runnable=False,
            code="""Sheet 1 "Revenue trend":   Columns = MONTH(Order Date) [continuous]   Rows = SUM(Completed Rev)
                            Marks = Line; add a reference line at the monthly target (parameter)
Sheet 2 "Category margin":  Rows = Category Name   Columns = Margin %   sort descending; colour = Margin % (diverging at 35%)
Sheet 3 "Region map/bar":   Rows = Region   Columns = SUM(Completed Rev)   label = Revenue YoY %
Dashboard: Region filter (all sheets) + filter action: click Category -> filter Revenue trend""",
            explanation="Use the Tableau workshop to download the CSVs and the brief, then verify your workbook against the expected totals shown there.",
        ),
        knowledge_check=["q_vz_016", "q_vz_017"],
        guided_exercise=None,
        challenge=None,
        tool_workshop="tableau",
        summary=[
            "Relationships keep tables at their own grain; prefer them to physical joins.",
            "Dimensions slice, measures aggregate; discrete = headers, continuous = axes.",
            "Calculated fields and LOD expressions encode business logic.",
            "Dashboards combine sheets with filters, actions and parameters.",
        ],
        common_mistakes=[
            "Physical joins that duplicate order-level values.",
            "Aggregating ratios with SUM instead of computing them from sums.",
            "Filters that apply only to one sheet unexpectedly.",
        ],
        revision="Complete the Tableau workshop and record your self-check.",
        next_lesson="vz7",
        order=31,
    ),
    Lesson(
        id="vz7",
        module="visualization",
        level="Intermediate",
        title="Looker Studio workflow: data sources, metrics and interactive reports",
        tools=["Looker Studio"],
        minutes=40,
        competencies=["storytelling", "chart_selection"],
        objectives=[
            "Prepare CSV/Google Sheets data for Looker Studio.",
            "Configure dimensions, metrics, aggregations and calculated fields.",
            "Build charts, scorecards and interactive controls.",
            "Share and document a report responsibly.",
        ],
        concept="""
> This lesson is a **guided assignment** for Looker Studio (formerly Google Data Studio; free, browser-based, requires a Google account). The lab does not connect to Google; it provides prepared data, step-by-step tasks and expected numbers to verify your report.

**Prepare the data.** Looker Studio works best with one flat, tidy table per data source. The workshop provides `looker_retail_lines.csv` - one row per completed order line with revenue, cost, category, region and date already joined (no double counting). Upload it via *Create -> Data source -> File Upload* or import it into Google Sheets first.

**Configure fields.** In the data source editor check each field's **type** (Date, Number, Text, Geo) and **default aggregation** (Sum, Average, Count Distinct). Set `order_date` to *Date (YYYYMMDD)*, `revenue` and `cost` to *Currency (EUR)* with Sum, `order_id` to *Count Distinct* when used as a metric.

**Calculated fields:**

```
Gross margin %   = (SUM(revenue) - SUM(cost)) / SUM(revenue)
AOV              = SUM(revenue) / COUNT_DISTINCT(order_id)
Revenue band     = CASE WHEN revenue >= 200 THEN "High" WHEN revenue >= 50 THEN "Medium" ELSE "Low" END
```

Ratios must aggregate numerator and denominator separately - define them with SUM inside the formula.

**Build the report:** *Scorecards* for KPIs (with comparison date range for % change), a *time series* for revenue, a *bar chart* for categories, a *geo chart* or table for regions. Add **controls**: date range control, drop-down list for region, and enable *cross-filtering* on charts.

**Share responsibly:** viewer access by default, a text box documenting definitions and data freshness, and no personal data in shared reports.
""",
        business_context="""
Northwind's marketing team uses Google Workspace and wants a self-service Looker Studio report on 2024 performance by region and category.
""",
        worked_example=WorkedExample(
            language="text",
            runnable=False,
            code="""Page layout (landscape 1200 x 900)
Row 1: Date range control | Region drop-down | Category drop-down
Row 2: Scorecards - Revenue | Orders (COUNT_DISTINCT order_id) | AOV | Gross margin %   (compare: previous period)
Row 3: Time series - revenue by month (dimension order_date, granularity Year Month)
Row 4: Bar chart - revenue by category (sorted) | Table - region, revenue, margin %, orders
Footer text: "Revenue = completed order lines after discounts, excludes shipping. Data: lab dataset, 2023-2024." """,
            explanation="Download the prepared CSV and brief in the Looker Studio workshop; compare your scorecards with the expected values.",
        ),
        knowledge_check=["q_vz_018", "q_vz_019"],
        guided_exercise=None,
        challenge=None,
        tool_workshop="looker",
        summary=[
            "Feed Looker Studio a flat, tidy, correctly typed table.",
            "Set default aggregations; define ratios from sums.",
            "Scorecards with comparisons, time series and controls make reports interactive.",
            "Document definitions and freshness in the report itself.",
        ],
        common_mistakes=[
            "Averaging a pre-computed margin column.",
            "Wrong field types (dates as text) breaking time series.",
            "Sharing edit access by default.",
        ],
        revision="Complete the Looker Studio workshop and the self-check rubric.",
        next_lesson=None,
        order=32,
    ),
]
