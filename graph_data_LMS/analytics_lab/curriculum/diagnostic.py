"""Module 2 - Diagnostic Analytics (Python, R, SQL)."""

from analytics_lab.models import Lesson, WorkedExample

LESSONS = [
    Lesson(
        id="dg1",
        module="diagnostic",
        level="Beginner",
        title="Data quality checks and exploratory data analysis",
        tools=["Python", "SQL"],
        minutes=40,
        competencies=["data_quality"],
        objectives=[
            "Run a systematic data-quality checklist before analysing.",
            "Quantify missing values and decide how to treat them.",
            "Detect duplicate entities, not just duplicate rows.",
            "Identify outliers with robust rules (IQR, median absolute deviation) and judge whether they are errors.",
        ],
        concept="""
Diagnosis begins with trust in the data. A quick, repeatable **data-quality checklist**:

1. **Shape & grain** - how many rows; what does one row represent; is the key unique?
2. **Types** - are dates parsed as dates and numbers as numbers?
3. **Missing values** - how many per column, and *why* (not collected, not applicable, failed join)?
4. **Duplicates** - identical rows, and duplicate *entities* with different IDs (same email, same name and address).
5. **Validity** - impossible values (negative quantities, ship date before order date, ages over 120).
6. **Consistency** - categories spelled differently (`'west'`, `'West '`), totals that do not reconcile.
7. **Distributions & outliers** - compare mean vs median; inspect extremes.

**Missing data mechanisms.** *MCAR* (missing completely at random) is harmless apart from lost precision; *MAR* (depends on observed variables) and *MNAR* (depends on the missing value itself, e.g. unhappy customers skip surveys) can bias results. Dropping rows is only safe under MCAR.

**Outlier rules.** The IQR rule flags values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR. Robust rules are preferred over mean +/- 3 SD because the mean and SD are themselves distorted by outliers. An outlier is a *question*, not an error: bulk B2B orders are real; a quantity of 99,999 is probably a data-entry error.

**EDA** then summarises distributions (histograms, box plots), relationships (scatter plots, correlation) and segments (group-by summaries). Write down what surprised you - those are hypotheses for later.
""",
        business_context="""
Before investigating Northwind's regional revenue drop, the analytics lead asks you to certify the `customers` and `order_items` tables. The marketing team claims "3,030 customers", but you suspect duplicate records and a few extreme orders.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"customers": "retail.customers", "items": "retail.order_items"},
            code="""# 1) Shape, types and missing values
print(customers.shape)
print(customers.dtypes)
print(customers.isna().sum().loc[lambda s: s > 0])

# 2) Is the key unique? Are there duplicate *people*?
print("unique ids:", customers.customer_id.is_unique)
dupe_people = customers.email_hash.duplicated(keep=False)
print("records sharing an email_hash:", dupe_people.sum())

# 3) Outliers in quantity with the IQR rule
q1, q3 = items.quantity.quantile([0.25, 0.75])
upper = q3 + 1.5 * (q3 - q1)
print(f"IQR upper fence: {upper}; lines above: {(items.quantity > upper).sum()}")
print(items.quantity.describe())""",
            explanation="""
* `customer_id` is unique, yet some `email_hash` values repeat: the **key** is clean but the **entity** is duplicated. Counting customers by ID overstates the customer base.
* `birth_year` has missing values. Age-based analysis would cover only customers who chose to share it - likely not a random subset.
* The quantity distribution is very skewed. With most lines at 1-2 units, the IQR fence is low; inspect the extremes (20-60 units) before deciding - they look like legitimate bulk purchases, so keep them but report medians alongside means.
""",
        ),
        knowledge_check=["q_dg_001", "q_dg_002", "q_dg_003"],
        guided_exercise="ex_py_dg1_quality",
        challenge="ex_py_dg1_outliers",
        summary=[
            "Check grain, types, missingness, duplicates, validity, consistency and distributions first.",
            "Unique keys do not guarantee unique entities.",
            "Missing data can be informative (MNAR); dropping rows can bias results.",
            "Outliers need judgement: investigate, then keep, cap or exclude - and document it.",
        ],
        common_mistakes=[
            "Dropping all rows with any NULL.",
            "Deleting outliers automatically.",
            "Trusting record counts as entity counts.",
        ],
        revision="Re-run the checklist on `subscription.support_tickets` and write one sentence per check.",
        next_lesson="dg2",
        order=8,
    ),
    Lesson(
        id="dg2",
        module="diagnostic",
        level="Intermediate",
        title="Segmentation and root-cause analysis",
        tools=["SQL", "Python"],
        minutes=45,
        competencies=["segmentation_rca", "kpi_reporting"],
        objectives=[
            "Frame a root-cause investigation as a tree of testable hypotheses.",
            "Drill down a KPI change by dimensions to localise it.",
            "Separate mix effects from rate effects.",
            "Distinguish supported findings from hypotheses that need more evidence.",
        ],
        concept="""
Root-cause analysis (RCA) is structured elimination.

**1. Confirm the change is real.** Is it a data issue (pipeline delay, definition change, duplicate load)? Compare with an independent source.

**2. Decompose the KPI.** Revenue = Orders x AOV; Orders = Visitors x Conversion. Which driver moved?

**3. Localise with drill-downs.** Slice the change by region, category, channel, customer segment and time. Look for the slice that explains most of the change (*contribution*), not the one with the largest percentage change (small segments swing wildly).

```
contribution of segment = change in segment / total change
```

**4. Mix vs rate.** A total rate can move because segment rates changed (*rate effect*) or because the share of segments changed (*mix effect*). Example: overall margin falls because low-margin categories grew, even though each category's margin is unchanged.

**5. Form and test hypotheses.** For each candidate cause, state what evidence would confirm or refute it (e.g. *"if the drop is a stock-out, units for that category in that region should fall while other categories stay normal, and the drop should end when stock returns"*).

**6. Communicate with calibrated language.** "The data shows...", "this is consistent with...", "we have not yet ruled out..." Separate **findings** (supported by evidence) from **hypotheses** (plausible, untested).
""",
        business_context="""
Northwind's West region revenue fell sharply in August-September 2024 and recovered in October. The regional VP blames a competitor's promotion. Before anybody responds with price cuts, you need to localise the drop.
""",
        worked_example=WorkedExample(
            language="sql",
            search_path="retail",
            code="""-- Where did West revenue go? Compare Aug-Sep 2024 with Aug-Sep 2023 by category.
WITH rev AS (
    SELECT c.category_name, YEAR(o.order_date) AS yr,
           SUM(oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0))) AS revenue
    FROM orders o
    JOIN order_items oi USING (order_id)
    JOIN products p USING (product_id)
    JOIN categories c USING (category_id)
    WHERE o.status = 'Completed' AND o.region = 'West' AND MONTH(o.order_date) IN (8, 9)
    GROUP BY ALL
)
SELECT category_name,
       ROUND(SUM(revenue) FILTER (WHERE yr = 2023), 0) AS rev_2023,
       ROUND(SUM(revenue) FILTER (WHERE yr = 2024), 0) AS rev_2024,
       ROUND(SUM(revenue) FILTER (WHERE yr = 2024) - SUM(revenue) FILTER (WHERE yr = 2023), 0) AS change,
       ROUND(100 * (SUM(revenue) FILTER (WHERE yr = 2024) - SUM(revenue) FILTER (WHERE yr = 2023))
             / SUM(SUM(revenue) FILTER (WHERE yr = 2024) - SUM(revenue) FILTER (WHERE yr = 2023)) OVER (), 1) AS share_of_change_pct
FROM rev
GROUP BY category_name
ORDER BY change;""",
            explanation="""
* Electronics accounts for (more than) the entire decline while other categories are roughly stable or growing - the drop is **localised**, not region-wide.
* A competitor promotion would typically hit several categories; a near-total collapse of a single category in a single region for exactly two months is more consistent with **supply** (stock-out, listing error).
* **Finding:** West Electronics explains the decline. **Hypothesis (to verify with operations):** stock-out. Shares above 100% happen when other segments grew.
""",
        ),
        knowledge_check=["q_dg_004", "q_dg_005", "q_dg_006"],
        guided_exercise="ex_sql_dg2_west_drop",
        challenge="ex_py_dg2_mix_rate",
        summary=[
            "Confirm the change is real before explaining it.",
            "Decompose KPIs into drivers and localise by contribution, not percentage change.",
            "Separate mix effects from rate effects.",
            "Report findings and hypotheses separately, with the evidence needed to test each hypothesis.",
        ],
        common_mistakes=[
            "Chasing the segment with the largest % change even if it is tiny.",
            "Accepting the first plausible story (confirmation bias).",
            "Presenting hypotheses as conclusions.",
        ],
        revision="Write a hypothesis tree for the West drop with at least three branches and the evidence for each.",
        next_lesson="dg3",
        order=9,
    ),
    Lesson(
        id="dg3",
        module="diagnostic",
        level="Intermediate",
        title="Funnels, cohorts and retention",
        tools=["SQL", "Python"],
        minutes=45,
        competencies=["cohort_funnel"],
        objectives=[
            "Build a conversion funnel and find the biggest drop-off.",
            "Define cohorts and compare them at equal tenure.",
            "Compute retention and churn curves from subscription data.",
            "Recognise right-censoring in recent cohorts.",
        ],
        concept="""
**Funnels** measure how many users progress through ordered steps (visit -> sign-up -> activation -> purchase). Report both step conversion (step n / step n-1) and cumulative conversion (step n / step 1). Make sure each user is counted once per step and steps happen in order.

**Cohorts** group customers by a shared starting event, usually the signup month or quarter. Comparing cohorts answers: *are newer customers behaving differently from older ones?*

**Retention table.** Rows = cohort, columns = months since signup (tenure), cells = % of the cohort still active. Read **down a column** to compare cohorts at the same tenure; read **along a row** to see how one cohort decays.

**Churn rate** = customers lost during a period / customers at the start of the period. A *6-month churn rate* = share of a cohort that cancelled within 6 months of signup.

**Right-censoring.** A customer who signed up last month cannot have churned "within 6 months" yet. Comparing a recent cohort's churn-to-date with an old cohort's full 6-month churn makes recent cohorts look better than they are. Only compare cohorts that have been observed for the full window.

**Survivorship bias.** Analysing only currently active customers hides the ones who left - for example, "our customers love feature X" based on survivors.
""",
        business_context="""
CloudNest's leadership believes "retention has fallen". You need to verify this with a cohort view of 6-month churn and identify when the deterioration started.
""",
        worked_example=WorkedExample(
            language="sql",
            search_path="subscription",
            code="""-- 6-month churn by signup quarter (only cohorts observable for 6 months: churn_features is
-- already restricted to sign-ups up to 2024-09-30 and the data runs to 2025-03-31)
SELECT DATE_TRUNC('quarter', signup_date)  AS signup_quarter,
       COUNT(*)                            AS customers,
       SUM(churned_6m)                     AS churned,
       ROUND(100.0 * AVG(churned_6m), 1)   AS churn_6m_pct
FROM churn_features
GROUP BY 1
ORDER BY 1;""",
            explanation="""
* Churn sits around 23-26% for 2023 Q1 - 2024 Q1 cohorts and jumps to over 30% from 2024 Q2.
* Because every cohort is observed for a full 6 months, the comparison is fair (no right-censoring).
* **Next question:** what changed for customers acquired from Q2 2024? (Hint: look at `acquisition_source` and the Basic price change.)
""",
        ),
        extra_examples=[
            WorkedExample(
                language="python",
                preload={"months": "subscription.subscription_months", "subs": "subscription.subscriptions"},
                code="""# Retention matrix: % of each signup-quarter cohort active N months after signup
df = months.merge(subs[["customer_id", "signup_date"]], on="customer_id")
df["cohort"] = df.signup_date.dt.to_period("Q").astype(str)
df["tenure"] = (df.month.dt.year - df.signup_date.dt.year) * 12 + (df.month.dt.month - df.signup_date.dt.month)
size = subs.assign(cohort=subs.signup_date.dt.to_period("Q").astype(str)).groupby("cohort").size()
active = df.groupby(["cohort", "tenure"]).customer_id.nunique().unstack()
retention = active.div(size, axis=0).loc[:, [0, 1, 3, 6, 9, 12]].round(3) * 100
print(retention)""",
                explanation="Each row is a cohort; columns are months since signup. Blank cells for recent cohorts are right-censored - they have not reached that tenure yet.",
            )
        ],
        knowledge_check=["q_dg_007", "q_dg_008", "q_dg_009"],
        guided_exercise="ex_sql_dg3_cohort_churn",
        challenge="ex_py_dg3_retention",
        summary=[
            "Funnels need ordered, de-duplicated steps; report step and cumulative conversion.",
            "Compare cohorts at equal tenure (read down the retention columns).",
            "Exclude or flag cohorts that have not been observed for the full window.",
            "Beware survivorship bias when analysing current customers only.",
        ],
        common_mistakes=[
            "Comparing churn-to-date across cohorts of different ages.",
            "Using total active customers as the churn denominator mid-period.",
            "Counting users multiple times in a funnel step.",
        ],
        revision="Rebuild the retention matrix by acquisition source and compare Paid Social with Referral.",
        next_lesson="dg4",
        order=10,
    ),
    Lesson(
        id="dg4",
        module="diagnostic",
        level="Advanced",
        title="Correlation, confounding and Simpson's paradox",
        tools=["Python"],
        minutes=45,
        competencies=["causal_reasoning", "segmentation_rca"],
        objectives=[
            "Compute and interpret correlation and covariance (Pearson and Spearman).",
            "Explain why correlation does not imply causation.",
            "Identify confounders and composition effects.",
            "Detect Simpson's paradox by comparing aggregate and within-segment results.",
        ],
        concept="""
**Covariance** measures how two variables move together but depends on units. **Pearson correlation** standardises it to [-1, 1] and measures *linear* association; **Spearman** correlation uses ranks and captures monotonic relationships while being robust to outliers. r = 0 does not mean "no relationship" - a U-shape can have r near 0.

**Why correlation is not causation:**

* **Confounding:** a third variable drives both (ice-cream sales and drownings both rise with temperature).
* **Reverse causality:** unhappy customers file more tickets, rather than tickets causing unhappiness.
* **Selection effects:** analysing a filtered population (only customers who replied to a survey).
* **Chance:** test enough pairs and some will correlate by luck.

**Simpson's paradox / composition effects.** An aggregate trend can differ from - or even reverse - the trend within every segment, because segment *sizes* changed. Classic pattern: churn rises overall while churn *within each channel* is flat, because the mix shifted towards a high-churn channel.

**How to guard against it:** segment by plausible confounders; compare like with like (stratify or standardise to a fixed mix); state which variables you did *not* control for. Only randomised experiments (next lesson) cleanly identify causal effects; with observational data, use careful language.
""",
        business_context="""
CloudNest's 6-month churn rose from about 25% to over 30%. The product team says "the new onboarding flow broke something". The marketing team ran a big Paid Social campaign from April 2024. Who is right?
""",
        worked_example=WorkedExample(
            language="python",
            preload={"cf": "subscription.churn_features"},
            code="""cf["period"] = np.where(cf.signup_date < "2024-04-01", "before", "after")

overall = cf.groupby("period").churned_6m.mean()
print("Overall churn:", overall.round(3).to_dict())

by_source = cf.pivot_table(index="acquisition_source", columns="period", values="churned_6m", aggfunc="mean").round(3)
mix = pd.crosstab(cf.acquisition_source, cf.period, normalize="columns").round(3)
print(by_source)
print(mix)

# Standardise: apply 'after' churn rates to the 'before' mix
std = (by_source["after"] * mix["before"]).sum()
print(f"Churn after, at the old channel mix: {std:.3f}")""",
            explanation="""
* Overall churn rose noticeably.
* Within most channels, churn barely moved - but Paid Social's **share** of sign-ups jumped from ~15% to ~40%, and Paid Social churns at roughly twice the rate of other channels.
* Re-weighting the new rates to the old mix shows most of the increase disappears: a **composition effect**. The onboarding hypothesis is not supported by this evidence (though Basic customers also saw a price rise in July 2024 - check that separately).
""",
        ),
        knowledge_check=["q_dg_010", "q_dg_011", "q_dg_012"],
        guided_exercise="ex_py_dg4_simpson",
        challenge="ex_py_dg4_correlation",
        summary=[
            "Pearson measures linear association; Spearman is rank-based and robust.",
            "Confounding, reverse causality, selection and chance all produce correlations.",
            "Compare aggregate and within-segment results to detect composition effects.",
            "Standardising to a fixed mix quantifies how much of a change is due to mix.",
        ],
        common_mistakes=[
            "Recommending action from a correlation alone.",
            "Ignoring changes in segment mix over time.",
            "Concluding 'no relationship' from r near 0.",
        ],
        revision="Repeat the standardisation using plan instead of acquisition source.",
        next_lesson="dg5",
        order=11,
    ),
    Lesson(
        id="dg5",
        module="diagnostic",
        level="Advanced",
        title="Hypothesis testing, confidence intervals and A/B tests",
        tools=["Python"],
        minutes=55,
        competencies=["statistical_inference"],
        objectives=[
            "State null and alternative hypotheses for a business question.",
            "Interpret p-values and confidence intervals correctly.",
            "Run a two-proportion z-test and Welch's t-test.",
            "Distinguish statistical from practical significance and check test assumptions.",
        ],
        concept="""
**Hypothesis test logic.** Assume the null hypothesis H0 (no difference). Compute how surprising the observed data would be under H0. The **p-value** is the probability of a result at least as extreme as the one observed *if H0 were true*.

* A p-value is **not** the probability that H0 is true, nor the probability the result is due to chance.
* Choosing alpha = 0.05 means accepting a 5% false-positive rate when there is truly no effect.
* "Not significant" means "not enough evidence", not "no effect".

**Confidence intervals** are more informative than p-values: a 95% CI for the lift gives a plausible range of effect sizes. If the CI excludes 0, the result is significant at 5%. A wide CI means you need more data.

**Common tests**

| Question | Test |
|---|---|
| Difference in two conversion rates | two-proportion z-test (or chi-square) |
| Difference in two means (unequal variances) | Welch's t-test |
| Skewed metric, e.g. revenue per user | Mann-Whitney U or bootstrap CI |
| Association of two categorical variables | chi-square test of independence |

**A/B testing essentials:** randomise; decide the primary metric, minimum detectable effect and sample size *before* starting; do not stop early when p dips below 0.05 ("peeking" inflates false positives); check sample-ratio mismatch (are groups the expected size?); beware novelty effects and multiple comparisons across many segments.

**Practical significance.** With 1 million users, a 0.05 percentage-point lift can be "significant" but worthless. Compare the CI with the smallest effect that would justify the cost of the change.

**Assumptions & limitations.** Independence of observations, adequate sample sizes (expected counts >= 5-10 per cell), and no interference between groups. Report them.
""",
        business_context="""
CloudNest's sister e-commerce team tested a redesigned checkout on 20,000 users. Conversion went from about 10.1% to 10.7%. The product manager wants to roll it out. Is the lift real, how big might it be, and is it worth it?
""",
        worked_example=WorkedExample(
            language="python",
            preload={"ab": "marketing.ab_test"},
            code="""from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep

g = ab.groupby("variant").converted.agg(["sum", "count", "mean"])
print(g)

conv = g.loc[["treatment", "control"], "sum"].values
n = g.loc[["treatment", "control"], "count"].values
z, p = proportions_ztest(conv, n)
lo, hi = confint_proportions_2indep(conv[0], n[0], conv[1], n[1], method="wald")
lift = g.loc["treatment", "mean"] - g.loc["control", "mean"]
print(f"lift = {lift:.4f} ({lift / g.loc['control', 'mean']:.1%} relative); z = {z:.2f}; p = {p:.4f}")
print(f"95% CI for the difference: [{lo:.4f}, {hi:.4f}]")

# Novelty check: does the lift persist after week 1?
print(ab.pivot_table(index="week", columns="variant", values="converted", aggfunc="mean").round(4))""",
            explanation="""
* The absolute lift is about 0.6 percentage points (~6% relative). The p-value is around 0.15 and the 95% CI includes 0, so the evidence is **not** strong enough to claim an effect at the 5% level.
* Week 1 shows a larger treatment advantage than later weeks - consistent with a novelty effect.
* **Recommendation:** do not claim a win. Either extend the test (the CI is wide) or decide whether the plausible range of lifts justifies rollout costs.
""",
        ),
        knowledge_check=["q_dg_013", "q_dg_014", "q_dg_015", "q_dg_016"],
        guided_exercise="ex_py_dg5_abtest",
        challenge="ex_py_dg5_welch",
        summary=[
            "A p-value measures surprise under H0 - not the probability that H0 is true.",
            "Confidence intervals show the plausible size of the effect; prefer them in reports.",
            "Pre-register metric and sample size; do not peek and stop early.",
            "Statistical significance is not business significance.",
        ],
        common_mistakes=[
            "Saying 'there is a 95% chance the effect is real'.",
            "Testing 20 segments and reporting the one with p < 0.05.",
            "Using a t-test on heavily skewed revenue without checking robustness.",
        ],
        revision="Compute the CI by device and explain why segment-level CIs are wider.",
        next_lesson="dg6",
        order=12,
    ),
    Lesson(
        id="dg6",
        module="diagnostic",
        level="Professional",
        title="Anomaly detection and communicating evidence",
        tools=["Python", "SQL"],
        minutes=45,
        competencies=["segmentation_rca", "statistical_inference", "causal_reasoning"],
        objectives=[
            "Detect anomalies in time series with rolling statistics and seasonal baselines.",
            "Distinguish anomalies from expected seasonality and known events.",
            "Write a diagnostic memo with findings, evidence, limitations and alternatives.",
        ],
        concept="""
**Anomaly detection** asks: is this observation unusual *relative to what we expected*?

* **Static thresholds** (revenue < EUR 10k) are simple but ignore seasonality.
* **Rolling z-score:** compare each value with the mean and SD of a trailing window (e.g. the previous 28 days). Flag |z| > 3. Use the *trailing* window so today's value does not influence its own baseline.
* **Seasonal baselines:** compare with the same weekday in previous weeks, or model trend + seasonality and flag large residuals.
* **Robust statistics** (median, MAD) resist contamination by earlier anomalies.

Every detector trades off false alarms against missed incidents. Tune thresholds with historical incidents and consider the cost of each error.

**Communicating evidence - the diagnostic memo**

1. **Question & answer first** - "West revenue fell ~39% in Aug-Sep versus last year; the Electronics collapse (-EUR 42k) more than explains it, while other categories grew."
2. **Evidence** - the 2-3 analyses that support it, with numbers and charts.
3. **Confidence & limitations** - data gaps, untested assumptions, possible confounders.
4. **Alternative explanations considered** - and why they are less consistent with the data.
5. **Next steps** - what would confirm the hypothesis (e.g. inventory records), and recommended actions.

Use calibrated language: *shows*, *is consistent with*, *suggests*, *we cannot rule out*.
""",
        business_context="""
Operations wants an automatic alert when daily demand for a SKU is abnormal, and leadership wants a short memo explaining the West revenue incident. Both require separating real signals from normal variation.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"dd": "operations.daily_demand"},
            code="""# Total daily demand with a trailing 28-day rolling z-score
daily = dd.groupby("date").units_demanded.sum().sort_index()
roll = daily.shift(1).rolling(28, min_periods=28)
z = (daily - roll.mean()) / roll.std()
flags = z[abs(z) > 3]
print(f"{len(flags)} anomalous days out of {z.notna().sum()}")
print(flags.round(2).head(10))

# Compare with a weekday-aware baseline: same weekday, previous 4 weeks
wk_base = pd.concat([daily.shift(7 * k) for k in range(1, 5)], axis=1).median(axis=1)
ratio = (daily / wk_base).dropna()
print(ratio.describe().round(3))""",
            explanation="""
* The trailing window (`shift(1)`) ensures each day is judged against the past only.
* Demand has strong weekly seasonality (weekends are low), so a plain rolling z-score flags days that are simply Sundays near holidays. The weekday-aware ratio is usually a better baseline.
* Before alerting, ask whether flagged days coincide with known events (promotions, holidays).
""",
        ),
        knowledge_check=["q_dg_017", "q_dg_018", "q_dg_019"],
        guided_exercise="ex_py_dg6_anomaly",
        challenge=None,
        summary=[
            "Anomalies are deviations from an expected baseline - choose the baseline carefully.",
            "Use trailing windows and robust statistics; account for seasonality.",
            "Memos lead with the answer, then evidence, limitations, alternatives and next steps.",
            "Calibrate language to the strength of evidence.",
        ],
        common_mistakes=[
            "Centred windows that leak the current value into its own baseline.",
            "Flagging normal seasonal peaks as anomalies.",
            "Writing memos that list analyses but never answer the question.",
        ],
        revision="Write a 5-sentence memo on the A/B test result using the memo structure.",
        next_lesson="dg7",
        order=13,
    ),
    Lesson(
        id="dg7",
        module="diagnostic",
        level="Intermediate",
        title="R for diagnostic analysis",
        tools=["R"],
        minutes=40,
        competencies=["r_programming", "statistical_inference"],
        objectives=[
            "Work with vectors and data frames in R.",
            "Group and summarise with base R (aggregate, tapply) and dplyr.",
            "Visualise distributions with ggplot2 (optional package).",
            "Run t-tests and chi-square tests in R and read their output.",
        ],
        concept="""
R is designed for statistics; many tests are one function call. Key differences from Python:

* Indexing starts at **1**, not 0. `x[1]` is the first element.
* Vectors are the basic type: `x <- c(3, 5, 8)`; operations are vectorised: `x * 2`.
* Data frames: `df$column`, `df[rows, cols]`, `nrow(df)`, `summary(df)`, `str(df)`.
* Missing values are `NA`; most functions need `na.rm = TRUE`: `mean(x, na.rm = TRUE)`.
* Assignment uses `<-` (`=` also works).

**Base R grouping**

```r
aggregate(churned_6m ~ acquisition_source, data = cf, FUN = mean)
tapply(cf$churned_6m, cf$plan, mean)
table(cf$plan, cf$churned_6m)          # contingency table
```

**dplyr (tidyverse)** - readable pipelines:

```r
library(dplyr)
cf |>
  group_by(acquisition_source) |>
  summarise(customers = n(), churn = mean(churned_6m)) |>
  arrange(desc(churn))
```

**ggplot2** - grammar of graphics:

```r
library(ggplot2)
ggplot(cf, aes(x = logins_first_month, fill = factor(churned_6m))) +
  geom_histogram(bins = 30, position = "identity", alpha = 0.5) +
  labs(x = "Logins in first month", fill = "Churned")
```

**Tests:** `t.test(y ~ group, data = df)` runs Welch's t-test by default; `chisq.test(table(a, b))`; `prop.test(x = c(k1, k2), n = c(n1, n2))`; `cor.test(x, y, method = "spearman")`.

In the lab, graded R exercises use **base R only** so they work without extra packages. `load_table("subscription.churn_features")` reads a dataset as a data frame (dates arrive as text - convert with `as.Date()`).
""",
        business_context="""
CloudNest's data science team works in R. You are asked to reproduce the churn-by-source summary and test whether early engagement differs between churners and non-churners, in R.
""",
        worked_example=WorkedExample(
            language="r",
            preload={"cf": "subscription.churn_features"},
            code="""# Churn rate by acquisition source (base R)
agg <- aggregate(churned_6m ~ acquisition_source, data = cf, FUN = mean)
agg <- agg[order(-agg$churned_6m), ]
print(agg)

# Do churners log in less in their first month? Welch t-test
print(t.test(logins_first_month ~ churned_6m, data = cf))

# Is churn associated with plan? Chi-square test
print(chisq.test(table(cf$plan, cf$churned_6m)))""",
            explanation="""
* `aggregate(y ~ g, data, FUN)` is base R's GROUP BY.
* `t.test` uses Welch's correction by default (`var.equal = FALSE`). Read the means of both groups, the CI for the difference and the p-value.
* `chisq.test` on a contingency table tests whether churn rates differ across plans.
* Requires a local R installation; if R is not installed the lab shows installation instructions and this example cannot run.
""",
        ),
        knowledge_check=["q_dg_020", "q_dg_021"],
        guided_exercise="ex_r_dg7_summary",
        challenge="ex_r_dg7_ttest",
        summary=[
            "R indexes from 1, uses NA for missing values and is vectorised.",
            "aggregate()/tapply() in base R and group_by()/summarise() in dplyr perform grouped summaries.",
            "t.test(), chisq.test(), prop.test() and cor.test() cover most diagnostic tests.",
            "Python and R give the same statistics when the same method and options are used - check defaults.",
        ],
        common_mistakes=[
            "Forgetting na.rm = TRUE and getting NA results.",
            "Assuming R's t.test defaults match scipy's (scipy's ttest_ind assumes equal variances unless equal_var=False).",
            "Treating text dates as dates without as.Date().",
        ],
        revision="Translate the Python Simpson's-paradox example (dg4) into R.",
        next_lesson="pr1",
        order=14,
    ),
]
