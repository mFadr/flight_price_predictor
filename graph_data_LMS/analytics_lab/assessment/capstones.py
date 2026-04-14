"""Five integrative capstone projects with milestones and automated checks."""

from __future__ import annotations

from analytics_lab.models import Capstone, Check, Exercise, Milestone, RubricCriterion

SQL_RUBRIC = [("Result set matches the expected rows and values", 60), ("Correct columns and names", 20), ("Correct number of rows", 20)]

LEVELS_STD = ["Missing or incorrect", "Partially addresses the criterion", "Solid and mostly complete", "Excellent, precise and well justified"]


def _crit(name: str, desc: str, weight: float = 1.0) -> RubricCriterion:
    return RubricCriterion(name, desc, LEVELS_STD, weight)


CAPSTONE_EXERCISES = [
    Exercise(
        id="ex_cap1_region_scorecard",
        title="Capstone 1 - Regional scorecard",
        module="descriptive", language="sql", difficulty="Professional", topic="KPI scorecard",
        competencies=["kpi_reporting", "sql_joins", "sql_aggregation"], kind="capstone",
        business_question="Produce the regional scorecard for the annual performance review.",
        dataset="retail", tables=["retail.orders", "retail.order_items", "retail.products"], search_path="retail",
        requirements=[
            "Completed orders. One row per region.",
            "Columns: `region`, `revenue_2023`, `revenue_2024` (2 dp), `yoy_growth_pct` (1 dp), `margin_pct_2024` (1 dp), `aov_2024` (2 dp).",
            "margin_pct_2024 = 100 * (revenue - cost) / revenue for 2024; cost = quantity * products.unit_cost; aov_2024 = 2024 revenue / distinct 2024 orders.",
            "Order by revenue_2024 descending.",
        ],
        expected_output="5 rows x 6 columns.",
        starter_code="WITH lines AS (\n    SELECT o.region, o.order_id, YEAR(o.order_date) AS yr,\n           oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0)) AS revenue,\n           oi.quantity * p.unit_cost AS cost\n    FROM orders o\n    JOIN order_items oi ON oi.order_id = o.order_id\n    JOIN products p ON p.product_id = oi.product_id\n    WHERE o.status = 'Completed'\n)\nSELECT region FROM lines GROUP BY region;\n",
        solution="WITH lines AS (\n    SELECT o.region, o.order_id, YEAR(o.order_date) AS yr,\n           oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0)) AS revenue,\n           oi.quantity * p.unit_cost AS cost\n    FROM orders o\n    JOIN order_items oi ON oi.order_id = o.order_id\n    JOIN products p ON p.product_id = oi.product_id\n    WHERE o.status = 'Completed'\n), agg AS (\n    SELECT region,\n           SUM(revenue) FILTER (WHERE yr = 2023) AS r23,\n           SUM(revenue) FILTER (WHERE yr = 2024) AS r24,\n           SUM(cost) FILTER (WHERE yr = 2024) AS c24,\n           COUNT(DISTINCT order_id) FILTER (WHERE yr = 2024) AS o24\n    FROM lines GROUP BY region\n)\nSELECT region,\n       ROUND(r23, 2) AS revenue_2023,\n       ROUND(r24, 2) AS revenue_2024,\n       ROUND(100 * (r24 / r23 - 1), 1) AS yoy_growth_pct,\n       ROUND(100 * (r24 - c24) / r24, 1) AS margin_pct_2024,\n       ROUND(r24 / o24, 2) AS aov_2024\nFROM agg\nORDER BY revenue_2024 DESC;",
        explanation="Conditional aggregation computes several period metrics in one pass; ratios are computed from unrounded sums.",
        hints=["SUM(revenue) FILTER (WHERE yr = 2024) gives 2024 revenue per region.", "COUNT(DISTINCT order_id) FILTER (...) counts orders at line grain.", "Compute ratios in the final SELECT from the aggregated components."],
        order_matters=True, rubric=SQL_RUBRIC,
    ),
    Exercise(
        id="ex_cap2_price_effect",
        title="Capstone 2 - Isolate the price effect (difference-in-differences)",
        module="diagnostic", language="python", difficulty="Professional", topic="Difference-in-differences",
        competencies=["causal_reasoning", "segmentation_rca", "cohort_funnel"], kind="capstone",
        business_question="The Basic price rose in July 2024 at the same time as the Paid Social push. Estimate the price effect on 6-month churn while removing the channel-mix effect.",
        dataset="subscription", tables=["subscription.churn_features"], preload={"cf": "subscription.churn_features"},
        requirements=[
            "Exclude Paid Social customers (removes the mix shift).",
            "`after` = signup_date >= 2024-04-01 (their first 6 months include the July price change); before = earlier sign-ups.",
            "`rates`: DataFrame of churn rate with index plan_group ('Basic', 'Other') and columns 'before', 'after'.",
            "`did` = (Basic after - Basic before) - (Other after - Other before).",
        ],
        expected_output="A 2x2 table and one float.",
        starter_code="d = cf[cf['acquisition_source'] != 'Paid Social'].copy()\nd['plan_group'] = np.where(d['plan'] == 'Basic', 'Basic', 'Other')\nd['period'] = np.where(d['signup_date'] >= '2024-04-01', 'after', 'before')\n\nrates = None\ndid = None\n",
        solution="d = cf[cf['acquisition_source'] != 'Paid Social'].copy()\nd['plan_group'] = np.where(d['plan'] == 'Basic', 'Basic', 'Other')\nd['period'] = np.where(d['signup_date'] >= '2024-04-01', 'after', 'before')\nrates = d.pivot_table(index='plan_group', columns='period', values='churned_6m', aggfunc='mean')[['before', 'after']]\ndid = (rates.loc['Basic', 'after'] - rates.loc['Basic', 'before']) - (rates.loc['Other', 'after'] - rates.loc['Other', 'before'])\n",
        explanation="Difference-in-differences compares the change for the affected group (Basic) with the change for an unaffected comparison group (Other plans), removing shared time trends. It assumes both groups would otherwise have moved in parallel - state that assumption.",
        hints=["pivot_table(index='plan_group', columns='period', values='churned_6m', aggfunc='mean').", "did = change in Basic minus change in Other."],
        checks=[
            Check("rates table", "r = need('rates', pd.DataFrame)\nrr = ref['rates']\nfor g in ['Basic', 'Other']:\n    for p in ['before', 'after']:\n        assert close(r.loc[g, p], rr.loc[g, p], tol=1e-9), f'rates.loc[{g!r}, {p!r}] is incorrect. Did you exclude Paid Social?'", weight=2),
            Check("did", "assert close(need('did'), ref['did'], tol=1e-9), 'did = (Basic after - Basic before) - (Other after - Other before).'", weight=2),
        ],
        visible_tests=["2x2 churn table", "Difference-in-differences estimate"],
        rubric=[("Mix effect removed", 30), ("Correct groups & periods", 30), ("Correct estimate", 40)],
    ),
    Exercise(
        id="ex_cap3_forecast",
        title="Capstone 3 - 8-week demand forecast with intervals",
        module="predictive", language="python", difficulty="Professional", topic="Forecasting with uncertainty",
        competencies=["forecasting", "responsible_ml"], kind="capstone",
        business_question="Forecast total daily demand for the final 56 days of 2024 using only earlier data, with an 80% prediction interval.",
        dataset="operations", tables=["operations.daily_demand"], preload={"dd": "operations.daily_demand"},
        requirements=[
            "`y`: total units_demanded per day; train = all but the last 56 days.",
            "Any method you like (seasonal naive, Holt-Winters, regression with calendar features...), trained on train only.",
            "`forecast`, `lower`, `upper`: arrays of length 56 for the last 56 days (80% interval).",
            "The forecast must beat the seasonal-naive MAE; the interval should cover roughly 80% of actual days (60-95% accepted).",
        ],
        expected_output="Three arrays of length 56.",
        starter_code="y = dd.groupby('date')['units_demanded'].sum().sort_index().asfreq('D')\ntrain, test = y.iloc[:-56], y.iloc[-56:]\n\nforecast = lower = upper = None\n",
        solution="from statsmodels.tsa.holtwinters import ExponentialSmoothing\ny = dd.groupby('date')['units_demanded'].sum().sort_index().asfreq('D')\ntrain, test = y.iloc[:-56], y.iloc[-56:]\nfit = ExponentialSmoothing(train, trend='add', seasonal='add', seasonal_periods=7).fit()\nforecast = np.asarray(fit.forecast(56))\nresid = (train - fit.fittedvalues).dropna()\nq_lo, q_hi = np.quantile(resid[-365:], [0.10, 0.90])\nlower, upper = forecast + q_lo, forecast + q_hi\n",
        explanation="Holt-Winters with weekly seasonality typically beats seasonal naive by smoothing noise. Residual quantiles from the last year give a simple empirical interval; check its coverage on the holdout.",
        hints=["Seasonal naive = repeat the last 7 training days.", "statsmodels ExponentialSmoothing(train, trend='add', seasonal='add', seasonal_periods=7).", "Interval from residual quantiles: forecast + quantile(resid, 0.10/0.90)."],
        checks=[
            Check("shapes", "f, lo, hi = (np.asarray(need(n), dtype=float) for n in ('forecast', 'lower', 'upper'))\nassert f.shape == (56,) and lo.shape == (56,) and hi.shape == (56,), 'forecast, lower and upper must each have 56 values.'\nassert (lo <= f + 1e-9).all() and (f <= hi + 1e-9).all(), 'Need lower <= forecast <= upper.'"),
            Check("beats seasonal naive", "y = user['dd'].groupby('date')['units_demanded'].sum().sort_index()\ntrain, test = y.iloc[:-56], y.iloc[-56:]\nsn = np.tile(train.iloc[-7:].values, 8)\nmae_sn = np.mean(np.abs(test.values - sn))\nmae = np.mean(np.abs(test.values - np.asarray(need('forecast'), dtype=float)))\nassert mae < mae_sn, f'Your MAE {mae:.1f} does not beat seasonal naive ({mae_sn:.1f}).'", weight=2),
            Check("interval coverage", "y = user['dd'].groupby('date')['units_demanded'].sum().sort_index()\ntest = y.iloc[-56:].values\ncov = np.mean((test >= np.asarray(need('lower'))) & (test <= np.asarray(need('upper'))))\nassert 0.60 <= cov <= 0.95, f'Interval covers {cov:.0%} of actual days; aim for about 80%.'", weight=2),
        ],
        visible_tests=["Three arrays of 56 values with lower <= forecast <= upper", "MAE better than seasonal naive", "Interval coverage between 60% and 95%"],
        rubric=[("Leak-free training", 25), ("Beats strong baseline", 40), ("Calibrated uncertainty", 35)],
    ),
    Exercise(
        id="ex_cap4_scenarios",
        title="Capstone 4 - Budget scenario grid",
        module="prescriptive", language="python", difficulty="Professional", topic="Scenario analysis",
        competencies=["optimization_modeling", "decision_analysis"], kind="capstone",
        business_question="How does optimal profit respond to the total budget and to the risk policy?",
        dataset="marketing", tables=["marketing.channel_assumptions"], preload={"ca": "marketing.channel_assumptions"},
        requirements=[
            "Same model as lesson ps5 (maximise margin * spend; min/max spend; budget; average risk <= cap).",
            "Solve for every combination of budget in [300000, 400000, 500000] and risk cap in [0.30, 0.35, 0.40].",
            "`scenarios`: DataFrame with columns budget, risk_cap, profit (NaN when infeasible) - 9 rows.",
        ],
        expected_output="9 rows x 3 columns.",
        starter_code="from scipy.optimize import linprog\n\ndef solve(budget, risk_cap):\n    ...\n\nscenarios = None\n",
        solution="from scipy.optimize import linprog\ndef solve(budget, risk_cap):\n    A = np.vstack([np.ones(len(ca)), ca['risk_score'].values - risk_cap])\n    res = linprog(-ca['expected_margin_per_dollar'].values, A_ub=A, b_ub=[budget, 0.0], bounds=list(zip(ca['min_spend'], ca['max_spend'])), method='highs')\n    return -res.fun if res.status == 0 else np.nan\nrows = [(b, r, solve(b, r)) for b in [300000, 400000, 500000] for r in [0.30, 0.35, 0.40]]\nscenarios = pd.DataFrame(rows, columns=['budget', 'risk_cap', 'profit'])\n",
        explanation="A scenario grid shows where extra budget pays off and how much profit the risk policy costs: at EUR 300k the budget binds; above EUR 400k only a looser risk cap adds profit. Infeasible cells, when they occur (tight caps with large minimum commitments), are decision-relevant information too.",
        hints=["Write a function solve(budget, risk_cap) returning profit or NaN.", "res.status == 0 means an optimal solution was found.", "Use a list comprehension over both lists."],
        checks=[
            Check("scenario grid", "frames_match(need('scenarios', pd.DataFrame), ref['scenarios'], sort_by=['budget', 'risk_cap'], rtol=1e-6, atol=0.5)", weight=3),
        ],
        visible_tests=["9 scenarios with optimal profit (NaN if infeasible)"],
        rubric=[("Correct model", 40), ("Complete grid", 30), ("Infeasibility handled", 30)],
    ),
    Exercise(
        id="ex_cap5_overview_figure",
        title="Capstone 5 - Executive overview figure",
        module="visualization", language="python", difficulty="Professional", topic="Small multiples for executives",
        competencies=["storytelling", "viz_coding", "viz_integrity"], kind="capstone",
        business_question="Create the one-page executive figure answering four questions: revenue trend, category mix, churn by source, A/B result.",
        dataset="retail", tables=["retail.orders", "retail.order_items", "subscription.churn_features", "marketing.ab_test"],
        preload={"orders": "retail.orders", "items": "retail.order_items", "cf": "subscription.churn_features", "ab": "marketing.ab_test"},
        requirements=[
            "One figure with a 2x2 grid of axes (plt.subplots(2, 2)).",
            "Every panel has a title that states a finding (at least 4 words) and labelled axes.",
            "Bar panels start at zero. At least one panel shows uncertainty (error bars).",
            "A figure-level title (fig.suptitle).",
        ],
        expected_output="A 2x2 figure.",
        starter_code="fig, axes = plt.subplots(2, 2, figsize=(13, 8))\n(ax1, ax2), (ax3, ax4) = axes\n\n# 1) monthly revenue trend  2) revenue by category  3) churn by acquisition source  4) A/B conversion with CIs\n",
        solution="import matplotlib.ticker as mtick\nd = items.merge(orders, on='order_id').query(\"status == 'Completed'\")\nd['revenue'] = d['quantity'] * d['unit_price'] * (1 - d['discount_pct'].fillna(0))\nm = d.groupby(d['order_date'].dt.to_period('M'))['revenue'].sum()\nfig, axes = plt.subplots(2, 2, figsize=(13, 8))\n(ax1, ax2), (ax3, ax4) = axes\nax1.plot(m.index.to_timestamp(), m.values / 1e3, color='#2563eb'); ax1.set_ylim(bottom=0)\nax1.set(title='Revenue grows with December peaks', xlabel='Month', ylabel='Revenue (EUR k)')\nby_reg = d[d['order_date'].dt.year == 2024].groupby('region')['revenue'].sum().sort_values()\nax2.barh(by_reg.index, by_reg.values / 1e3, color='#64748b')\nax2.set(title='East and North lead 2024 revenue', xlabel='Revenue (EUR k)', ylabel='Region')\nr = cf.groupby('acquisition_source')['churned_6m'].mean().sort_values()\nax3.barh(r.index, r.values * 100, color=['#d55e00' if s == 'Paid Social' else '#b0b7c3' for s in r.index])\nax3.set(title='Paid Social churns about twice as often', xlabel='6-month churn (%)', ylabel='Source')\ng = ab.groupby('variant')['converted'].agg(['mean', 'count'])\nse = np.sqrt(g['mean'] * (1 - g['mean']) / g['count'])\nax4.bar(g.index, g['mean'] * 100, yerr=196 * se, capsize=6, color=['#94a3b8', '#2563eb']); ax4.set_ylim(0, 13)\nax4.set(title='Checkout test lift is not significant', xlabel='Variant', ylabel='Conversion (%)')\nfig.suptitle('Northwind & CloudNest: performance overview')\nfig.tight_layout()\n",
        explanation="Small multiples with action titles let executives read four findings in under a minute. Honest baselines and visible uncertainty keep the page trustworthy.",
        hints=["fig.suptitle('...') adds the overall title.", "Set ylim/xlim bottom to 0 for bar panels.", "ax.bar(..., yerr=1.96*se*100, capsize=5) adds error bars."],
        checks=[
            Check("2x2 layout", "assert figs, 'Create a figure.'\nf = figs[-1]\nassert len(f.axes) >= 4, f'Expected 4 panels, found {len(f.axes)}.'"),
            Check("action titles and labels", "f = figs[-1]\nfor i, a in enumerate(f.axes[:4]):\n    assert len(a.get_title().split()) >= 4, f'Panel {i + 1} needs a finding-style title (4+ words).'\n    assert a.get_xlabel().strip() and a.get_ylabel().strip(), f'Panel {i + 1} needs both axis labels.'", weight=2),
            Check("zero baselines for bars", "import matplotlib.patches as mp\nf = figs[-1]\nfor i, a in enumerate(f.axes[:4]):\n    bars = [p for p in a.patches if isinstance(p, mp.Rectangle)]\n    if len(bars) >= 2:\n        horiz = len({round(b.get_x(), 6) for b in bars}) == 1\n        lo = (a.get_xlim() if horiz else a.get_ylim())[0]\n        assert abs(lo) < 1e-9, f'Bars in panel {i + 1} must start at zero (axis starts at {lo:.2f}).'"),
            Check("uncertainty shown", "import matplotlib.container as mc\nf = figs[-1]\nassert any(isinstance(c, mc.ErrorbarContainer) for a in f.axes for c in a.containers), 'Show uncertainty in at least one panel (error bars).'"),
            Check("figure title", "f = figs[-1]\nassert f._suptitle is not None and f._suptitle.get_text().strip(), 'Add fig.suptitle(...).'"),
        ],
        visible_tests=["4 panels", "Finding-style titles and axis labels", "Zero baselines for bars", "Error bars present", "Figure title"],
        rubric=[("Answers the four questions", 30), ("Honest design", 30), ("Storytelling titles", 25), ("Uncertainty", 15)],
    ),
]

CAPSTONES: list[Capstone] = [
    Capstone(
        id="cap1",
        title="Retail Performance Intelligence",
        modules=["descriptive", "visualization"],
        competencies=["kpi_reporting", "sql_joins", "sql_window", "excel_analysis", "bi_modeling"],
        datasets=["retail"],
        brief="""
**Client:** Northwind Living leadership team. **Deadline:** annual performance review.

Leadership wants a complete picture of 2024 performance versus 2023: revenue, margin, order economics, regional performance, category mix and returns - plus a specification for a Power BI dashboard the regional managers will use monthly.

You will combine SQL (calculations), Excel (an auditable workbook for finance), descriptive statistics and dashboard design. The final deliverable is a short KPI report with business implications, not just numbers.
""",
        requirements=[
            "KPI definition cards for revenue, gross margin %, AOV, return rate and YoY growth.",
            "A regional scorecard computed in SQL (automated check).",
            "An Excel workbook that reproduces two KPIs with SUMIFS and passes the workbook checker.",
            "A Power BI data model and dashboard specification (fact/dimension tables, relationships, 5+ DAX measures, page layout).",
            "A one-page executive summary with three implications and one recommended action.",
        ],
        milestones=[
            Milestone("m1", "Define the KPIs", "Write KPI definition cards (formula, filters, grain, owner, target, caveats) for the five KPIs.", "text",
                      rubric=[_crit("Precision", "Formulas and filters are unambiguous (e.g. completed orders, discount handling)."), _crit("Business relevance", "Each KPI has an owner, a target and a decision it informs."), _crit("Caveats", "Known data pitfalls are acknowledged.")]),
            Milestone("m2", "Regional scorecard (SQL)", "Build the regional scorecard query.", "exercise", exercise_id="ex_cap1_region_scorecard"),
            Milestone("m3", "Excel workbook", "Complete the Excel workbook workshop (Practice & Coding Lab -> Tool workshops) and upload it to the checker.", "checklist",
                      checklist=["Inputs, calculations and checks are on separate, labelled areas", "SUMIFS results match the checker", "No hard-coded numbers inside formulas", "A reconciliation check compares the workbook total with the source total"]),
            Milestone("m4", "Power BI specification", "Write the data model and dashboard specification.", "text",
                      rubric=[_crit("Model", "Fact table at order-line grain; product, customer, calendar dimensions; one-to-many single-direction relationships."), _crit("Measures", "At least five correct DAX measures, including margin % and YTD."), _crit("Layout", "KPI cards, trend, breakdown and detail with sensible slicers and drill-downs.")]),
            Milestone("m5", "Executive summary", "One page: headline, three implications, one recommendation, limitations.", "text",
                      rubric=[_crit("Answer first", "The headline answers 'how did we do?' in one sentence with numbers."), _crit("Implications", "Explains what the numbers mean for the business (e.g. West stock-out cost, margin mix)."), _crit("Actionability", "A specific recommendation with owner and next step."), _crit("Honesty", "Limitations and data caveats are stated.")]),
        ],
        evaluation=["Correctness of calculations (automated SQL check, workbook checker)", "Precision of KPI definitions", "Quality of the BI model and measures", "Business insight and clarity of the executive summary"],
        strong_example="""
**Headline:** 2024 revenue grew ~5% to about EUR 3.15 M while gross margin held at ~Y%; growth came from more orders (+~7.5%) while AOV slipped ~2%.

**Implications**
1. *West Electronics stock-out (Aug-Sep) cost about EUR 42k* versus the same months of 2023 (EUR ~50k -> ~8k); the region otherwise grew in line with the company. Supply reliability, not demand, is the risk.
2. *Apparel's return rate (~12.6%) is roughly double the company average*, eroding margin by an estimated EUR N k in refunds.
3. *Mix shift towards Electronics* lifts revenue but slightly dilutes margin %.

**Recommendation:** Operations to introduce safety-stock alerts for top-20 Electronics SKUs in each region (owner: Head of Supply, by Q2).

**Limitations:** revenue excludes shipping; 0.5% of lines have unknown discounts (treated as 0%); 30 duplicate customer records were merged for customer counts.

**Power BI model:** Fact `order_items` (grain: order line) -> `orders` (as a degenerate dimension or merged), `products` (with category merged in), `customers`, `Calendar`. Measures: Revenue (SUMX), Cost, Margin % (DIVIDE), Orders (DISTINCTCOUNT), AOV, Revenue YTD (TOTALYTD), Revenue PY (SAMEPERIODLASTYEAR), YoY %.
""",
        prerequisites=["ds3", "ds4", "ds5", "ds6", "ds7"],
    ),
    Capstone(
        id="cap2",
        title="Customer Retention Investigation",
        modules=["diagnostic", "descriptive"],
        competencies=["cohort_funnel", "causal_reasoning", "segmentation_rca", "statistical_inference"],
        datasets=["subscription"],
        brief="""
**Client:** CloudNest leadership. **Question:** *Why has customer retention fallen, and what should we do about it?*

Recent cohorts churn noticeably more within six months. Product blames marketing's Paid Social campaign; marketing blames July's Basic price increase; finance suspects onboarding. You must separate these explanations with evidence, distinguish supported conclusions from hypotheses, and recommend next steps.
""",
        requirements=[
            "Cohort analysis of 6-month churn (SQL or Python) at equal tenure.",
            "Segment comparisons by acquisition source, plan and early engagement.",
            "Quantify the channel-mix (composition) effect.",
            "Estimate the price effect with difference-in-differences (automated check).",
            "A findings memo separating supported conclusions, hypotheses to test, and recommendations.",
        ],
        milestones=[
            Milestone("m1", "Cohort view", "Complete the cohort churn exercise (by quarter and plan).", "exercise", exercise_id="ex_sql_dg3_cohort_churn"),
            Milestone("m2", "Composition effect", "Quantify how much of the increase is due to channel mix.", "exercise", exercise_id="ex_py_dg4_simpson"),
            Milestone("m3", "Price effect", "Isolate the Basic price effect with difference-in-differences.", "exercise", exercise_id="ex_cap2_price_effect"),
            Milestone("m4", "Findings memo", "Write the memo: findings (with evidence), hypotheses (with how to test them), recommendations.", "text",
                      rubric=[_crit("Evidence", "Each finding cites a number from your analyses."), _crit("Calibrated claims", "Clearly separates supported findings from untested hypotheses; no causal overreach."), _crit("Alternatives", "Discusses alternative explanations and why they are more or less consistent with the data."), _crit("Recommendations", "Specific, testable next steps (e.g. experiment on onboarding for Paid Social users).")]),
        ],
        evaluation=["Correct cohort and churn definitions (equal tenure)", "Quantified composition and price effects", "Reasoning quality: confounding, assumptions, limitations", "Actionable, calibrated recommendations"],
        strong_example="""
**Finding 1 (supported):** 6-month churn rose from ~25% (2023-Q1 2024 cohorts) to ~32% (Q2-Q3 2024 cohorts).
**Finding 2 (supported):** Paid Social's share of sign-ups jumped from ~15% to ~40%, and Paid Social churns at ~50% vs ~20% elsewhere. Re-weighting to the old mix removes most of the increase - the rise is mainly a **composition effect**.
**Finding 3 (supported, with assumptions):** Excluding Paid Social, Basic customers' churn rose more than other plans after the price change (difference-in-differences of a few percentage points), assuming parallel trends.
**Hypothesis (not yet tested):** Paid Social users have lower first-month engagement, suggesting poor fit or weak onboarding for this audience. *Test:* a randomised onboarding variant for Paid Social sign-ups.
**Not supported:** a general onboarding failure - churn within established channels is stable.
**Recommendations:** (1) Evaluate Paid Social on 6-month retained revenue, not sign-ups; (2) run the onboarding experiment; (3) monitor Basic churn monthly and consider grandfathering existing customers.
**Limitations:** observational data; parallel-trends assumption; satisfaction data missing for many tickets.
""",
        prerequisites=["dg1", "dg3", "dg4", "dg5"],
    ),
    Capstone(
        id="cap3",
        title="Sales Forecasting",
        modules=["predictive"],
        competencies=["forecasting", "regression_modeling", "model_validation", "responsible_ml"],
        datasets=["operations", "marketing"],
        brief="""
**Client:** Meridian Supply planning team. **Question:** *How much demand should we plan for over the next eight weeks, and how confident are we?*

You will build a reproducible forecasting workflow: establish baselines, compare at least two approaches on a temporal holdout, quantify uncertainty and explain when the forecast should not be trusted.
""",
        requirements=[
            "Temporal holdout of the last 56 days; no information from the holdout used for training.",
            "At least two approaches compared against seasonal naive.",
            "An 80% prediction interval with checked coverage (automated check).",
            "A short model note: chosen method, accuracy, uncertainty, limitations, monitoring.",
        ],
        milestones=[
            Milestone("m1", "Baselines", "Complete the forecast baseline exercise.", "exercise", exercise_id="ex_py_pr5_forecast"),
            Milestone("m2", "Forecast with intervals", "Beat seasonal naive on the 56-day holdout with a calibrated 80% interval.", "exercise", exercise_id="ex_cap3_forecast"),
            Milestone("m3", "Model note", "Explain your final model choice for the planning team.", "text",
                      rubric=[_crit("Comparison", "Compares at least two methods with the same holdout and metric."), _crit("Uncertainty", "Explains the interval, its coverage and how planners should use it."), _crit("Limitations", "Mentions censored demand, promotions, drift and when to retrain.")]),
        ],
        evaluation=["Leak-free evaluation design", "Improvement over a strong baseline", "Calibrated uncertainty", "Clear communication of limitations"],
        strong_example="""
**Method:** additive Holt-Winters with weekly seasonality, trained on 2023-01-01 to 2024-11-05.
**Accuracy (56-day holdout):** MAE ~X units/day vs ~Y for seasonal naive (-Z%).
**Uncertainty:** empirical 80% interval from the last year's residuals covered 79% of holdout days. Plan staffing to the upper bound on Mondays (highest demand day).
**Limitations:** demand on stock-out days is estimated; promotions are not modelled (forecast will under-shoot promotion weeks); retrain monthly and alert if weekly MAE exceeds 1.3x the holdout MAE.
""",
        prerequisites=["pr1", "pr2", "pr5"],
    ),
    Capstone(
        id="cap4",
        title="Resource Allocation Optimization",
        modules=["prescriptive"],
        competencies=["optimization_modeling", "decision_analysis", "simulation_risk"],
        datasets=["marketing"],
        brief="""
**Client:** CMO, quarterly budget planning. **Question:** *How should we allocate next quarter's marketing budget to maximise expected profit within budget, channel and risk constraints?*

Define the objective and constraints, implement the model, run scenario and sensitivity analyses, and write a recommendation that states the assumptions and the conditions under which it would change.
""",
        requirements=[
            "Formulate decision variables, objective and constraints explicitly.",
            "Optimal allocation with shadow price of the budget (automated check).",
            "Scenario grid for budget and risk policy (automated check).",
            "Recommendation memo with assumptions, binding constraints and change conditions.",
        ],
        milestones=[
            Milestone("m1", "Base model", "Solve the base allocation with a risk policy.", "exercise", exercise_id="ex_py_ps5_budget"),
            Milestone("m2", "Scenarios", "Build the budget x risk-policy scenario grid.", "exercise", exercise_id="ex_cap4_scenarios"),
            Milestone("m3", "Recommendation", "Write the recommendation for the CMO.", "text",
                      rubric=[_crit("Decision", "States the allocation in plain language and numbers."), _crit("Assumptions", "Linear margins within ranges, risk scores, minimum commitments."), _crit("Sensitivity", "Uses shadow prices / scenarios to say when the recommendation changes."), _crit("Trade-offs", "Explains the profit cost of the risk policy.")]),
        ],
        evaluation=["Correct formulation", "Optimal, feasible solutions", "Insightful sensitivity and scenario analysis", "Clear, assumption-aware recommendation"],
        strong_example="""
**Decision:** Fund Search (EUR 120k), Social (EUR 90k), Email (EUR 25k) and Affiliate (EUR 50k) to their caps, Display to EUR 60k and Video to ~EUR 53k - about EUR 398k in total.
**Expected profit:** ~EUR 143k.
**Binding constraint:** the 0.35 risk policy, not the budget. The optimiser leaves ~EUR 2k unspent; the budget's shadow price is zero, so asking for more budget is pointless under the current policy. Relaxing the risk cap to 0.40 adds ~EUR 1.4k at EUR 400k and ~EUR 6k at EUR 500k; tightening it to 0.30 costs ~EUR 16k.
**Scenario insight:** at EUR 300k the budget binds and the risk policy is irrelevant (profit ~EUR 124k for every cap).
**Assumptions:** margins are linear within min/max spend (diminishing returns beyond caps), risk scores are subjective.
**Changes if:** the risk policy is revisited, Email margin falls below Search's, or Video's minimum commitment is renegotiated.
""",
        prerequisites=["ps1", "ps4", "ps5"],
    ),
    Capstone(
        id="cap5",
        title="Executive Analytics Portfolio",
        modules=["visualization", "descriptive", "diagnostic", "predictive", "prescriptive"],
        competencies=["storytelling", "viz_integrity", "chart_selection", "kpi_reporting", "causal_reasoning"],
        datasets=["retail", "subscription", "marketing"],
        brief="""
**Client:** Group executive team. **Question:** *What are the three most important things leadership should know and do next quarter?*

Take a business question from definition through data preparation, analysis and visualisation to a recommendation. Build a visualisation portfolio answering five business questions with appropriate charts, critique a misleading dashboard, and deliver an executive summary.
""",
        requirements=[
            "Five business questions, each answered with an appropriate, honest chart.",
            "Executive overview figure (automated check).",
            "Dashboard critique (Chart Critique workshop).",
            "Executive summary: context, complication, resolution, with uncertainty stated.",
        ],
        milestones=[
            Milestone("m1", "Question definition & data preparation", "Define five precise, measurable business questions and the data/metrics for each.", "checklist",
                      checklist=["Each question is specific and measurable", "Metric, dimension and filters stated for each", "Data-quality issues checked and documented", "Chart type chosen and justified per question"]),
            Milestone("m2", "Executive overview figure", "Build the 2x2 executive figure.", "exercise", exercise_id="ex_cap5_overview_figure"),
            Milestone("m3", "Dashboard critique", "Complete the Chart Critique workshop (Practice & Coding Lab -> Tool workshops).", "checklist",
                      checklist=["Identified all misleading elements", "Explained the effect of each on interpretation", "Proposed a concrete fix for each"]),
            Milestone("m4", "Executive summary", "Write the final summary and recommendations.", "text",
                      rubric=[_crit("Storyline", "Context -> complication -> resolution, answer first."), _crit("Evidence", "Each claim supported by a chart or number."), _crit("Uncertainty", "States confidence and limitations honestly."), _crit("Recommendations", "Three prioritised actions with owners.")]),
        ],
        evaluation=["Question quality", "Chart choice and integrity", "Storytelling and executive communication", "Honest treatment of uncertainty"],
        strong_example="""
**Context:** Both businesses grew in 2024 (retail revenue ~+5%, subscription sign-ups up strongly).
**Complication:** Growth quality is slipping - CloudNest's newer customers churn more, and Northwind lost ~EUR 42k to a regional stock-out.
**Resolution / actions:**
1. Re-target Paid Social on retained revenue; run an onboarding experiment (owner: CMO).
2. Introduce safety-stock alerts for top Electronics SKUs (owner: Head of Supply).
3. Do not roll out the checkout redesign yet; extend the test - the observed lift is within noise (owner: Product).
**Confidence:** findings 1-2 are well supported by the data; the A/B result is inconclusive by design.
""",
        prerequisites=["vz3", "vz4", "vz5"],
    ),
]

CAPSTONES_BY_ID = {c.id: c for c in CAPSTONES}
