"""Beginner-friendly glossary and tool cheat sheets (searchable reference library)."""

GLOSSARY: dict[str, str] = {
    "A/B test": "A randomised experiment comparing a control and a treatment version to estimate the causal effect of a change.",
    "Aggregate function": "A function that summarises many rows into one value, e.g. SUM, COUNT, AVG, MIN, MAX.",
    "Anomaly": "An observation that deviates substantially from an expected baseline (accounting for trend and seasonality).",
    "AOV (average order value)": "Revenue divided by the number of orders, computed from summed components.",
    "Baseline model": "A trivial model (majority class, mean, last value, seasonal naive) that any real model must beat.",
    "Binding constraint": "A constraint that is fully used at the optimum; relaxing it would improve the objective.",
    "Bootstrap": "Resampling the data with replacement many times to estimate the uncertainty of a statistic.",
    "Calibration": "Agreement between predicted probabilities and observed frequencies.",
    "Cardinality (relationship)": "How many rows on each side of a relationship match: one-to-one, one-to-many, many-to-many.",
    "CASE expression": "SQL's if/then/else logic used to create categories or conditional aggregates.",
    "Censoring (right-censoring)": "When the outcome has not yet been observed for some units (e.g. recent customers who may still churn).",
    "Churn rate": "Share of customers who cancel within a period or within a fixed time after signup.",
    "Cohort": "A group of customers who share a starting event, such as the month they signed up.",
    "Confidence interval": "A range of plausible values for an unknown parameter, computed with a stated confidence level (e.g. 95%).",
    "Confounder": "A variable that influences both the supposed cause and the outcome, creating a spurious association.",
    "Confusion matrix": "Table of true/false positives and negatives for a classifier at a given threshold.",
    "Contribution analysis": "Measuring how much each segment's change contributes to a total change.",
    "Cross-validation": "Repeatedly training and validating a model on different folds of the data to estimate performance.",
    "CTE (common table expression)": "A named subquery defined with WITH ... AS (...) that makes SQL readable step by step.",
    "DAX": "Data Analysis Expressions, the formula language of Power BI measures and calculated columns.",
    "Data drift": "A change in the distribution of model inputs after deployment.",
    "Concept drift": "A change in the relationship between inputs and the outcome over time.",
    "Data leakage": "Information in training data that would not be available at prediction time, inflating evaluation scores.",
    "Decision variable": "A quantity the decision maker controls in an optimisation model.",
    "Dimension": "An attribute used to group or filter metrics (region, month, product category).",
    "Dimension table": "A table describing entities (products, customers, dates) that facts refer to.",
    "Difference-in-differences": "Comparing the change over time in a treated group with the change in a comparison group to estimate an effect.",
    "Elasticity": "Percentage change in one variable associated with a 1% change in another (e.g. price elasticity of demand).",
    "EOQ": "Economic order quantity: the order size that minimises ordering plus holding cost.",
    "Fact table": "A table of measurable events (sales lines) at a defined grain, linked to dimension tables.",
    "Feature engineering": "Creating informative model inputs from raw data.",
    "Filter context": "In Power BI, the set of filters applied when a measure is evaluated.",
    "Funnel": "A sequence of steps users progress through, measuring conversion between steps.",
    "Grain": "What one row of a table represents (one order, one order line, one customer-month).",
    "HAVING": "SQL clause that filters groups after aggregation.",
    "Hypothesis test": "A procedure for assessing whether data are consistent with a null hypothesis.",
    "IQR (interquartile range)": "Q3 minus Q1; used in robust outlier rules.",
    "Join": "Combining rows from two tables using a key: INNER, LEFT, RIGHT, FULL.",
    "KPI": "Key performance indicator: a precisely defined metric tied to a business objective and owner.",
    "LOD expression": "Tableau's level-of-detail calculation that computes values at a specified grain ({ FIXED ... }).",
    "Linear programming": "Optimisation with a linear objective and linear constraints.",
    "MAE": "Mean absolute error: the average size of prediction errors.",
    "Measure (BI)": "A calculation evaluated at query time in the current filter context.",
    "Metric": "A quantity that is aggregated and tracked (revenue, orders, churn rate).",
    "Monte Carlo simulation": "Estimating outcome distributions by repeatedly sampling uncertain inputs.",
    "NULL": "SQL marker for a missing or unknown value; not equal to zero or empty text.",
    "Overfitting": "A model that fits noise in training data and generalises poorly.",
    "p-value": "Probability of observing data at least as extreme as the sample if the null hypothesis were true.",
    "Pipeline (ML)": "A chain of preprocessing steps and a model fitted together to prevent leakage.",
    "PivotTable": "Excel's interactive grouping and aggregation tool (rows, columns, values, filters).",
    "Precision": "Of the cases predicted positive, the share that are actually positive.",
    "Prediction interval": "A range expected to contain a future observation with a given probability.",
    "Recall": "Of the actual positive cases, the share the model identifies.",
    "Retention": "Share of a cohort still active after a given time.",
    "RMSE": "Root mean squared error: penalises large errors more than MAE.",
    "ROC-AUC": "Probability that a classifier ranks a random positive above a random negative.",
    "Safety stock": "Extra inventory held to protect against demand and lead-time variability.",
    "Seasonal naive forecast": "Forecast that repeats the value from the same season in the previous cycle (e.g. last week's same weekday).",
    "Segmentation": "Splitting data into meaningful groups to compare behaviour.",
    "Sensitivity analysis": "Studying how outputs change when inputs or assumptions change.",
    "Shadow price": "Change in the optimal objective per unit relaxation of a constraint.",
    "Simpson's paradox": "A trend that appears in aggregate but disappears or reverses within subgroups, due to changing group sizes.",
    "Star schema": "A data model with a central fact table surrounded by dimension tables.",
    "Statistical significance": "Evidence strong enough to reject the null hypothesis at a chosen level; not the same as practical importance.",
    "SUMIFS": "Excel function that sums values meeting several criteria.",
    "Survivorship bias": "Drawing conclusions only from units that 'survived' a selection process.",
    "Threshold (classification)": "The probability above which a case is labelled positive.",
    "Window function": "SQL function computed over a set of rows related to the current row without collapsing them.",
    "XLOOKUP": "Excel lookup function with exact match by default and flexible return ranges.",
}

CHEATSHEETS: dict[str, str] = {
    "SQL (DuckDB)": """
```sql
SELECT col, SUM(x) AS total                -- choose & compute
FROM schema.table AS t                     -- source
JOIN other o ON o.key = t.key              -- INNER / LEFT / FULL JOIN
WHERE t.date >= DATE '2024-01-01'          -- row filter
GROUP BY col                               -- or GROUP BY ALL
HAVING SUM(x) > 100                        -- group filter
ORDER BY total DESC LIMIT 10;

COUNT(*) | COUNT(col) | COUNT(DISTINCT col)
CASE WHEN cond THEN a WHEN c2 THEN b ELSE c END
COALESCE(x, 0)   NULLIF(x, 0)   x IS NULL
SUM(x) FILTER (WHERE cond)                 -- conditional aggregate
DATE_TRUNC('month', d)  YEAR(d)  MONTH(d)  d - INTERVAL 1 YEAR
WITH a AS (...), b AS (...) SELECT ...     -- CTEs
ROW_NUMBER() / RANK() / DENSE_RANK() OVER (PARTITION BY g ORDER BY v DESC)
LAG(x) OVER (ORDER BY month)               -- previous row
SUM(x) OVER (PARTITION BY yr ORDER BY m)   -- running total
AVG(x) OVER (ORDER BY m ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
QUALIFY rn <= 3                            -- filter on window result (DuckDB)
NOT EXISTS (SELECT 1 FROM t2 WHERE ...)    -- anti-join
```
""",
    "pandas": """
```python
df.head(); df.info(); df.describe(); df.dtypes; df.shape
df.isna().sum(); df.duplicated().sum(); df["c"].nunique()
df[df["status"] == "Completed"]                     # filter
df.loc[mask, ["a", "b"]]                            # rows & columns
df.assign(rev=df.q * df.p)                          # new column
df.groupby("g")["x"].agg(["sum", "mean", "count"])
df.pivot_table(index="r", columns="c", values="x", aggfunc="sum")
pd.crosstab(df.a, df.b, normalize="columns")
df.merge(other, on="key", how="left")
df.sort_values("x", ascending=False)
df["d"].dt.year / .dt.month / .dt.to_period("M")
df.set_index("date").resample("W")["x"].sum()
s.rolling(7).mean(); s.shift(1); s.pct_change()
pd.qcut(s, 4, labels=False); pd.cut(s, bins=[0, 10, 100])
```
""",
    "Statistics (SciPy / statsmodels)": """
```python
from scipy import stats
stats.ttest_ind(a, b, equal_var=False)              # Welch t-test
stats.mannwhitneyu(a, b)                            # non-parametric
stats.chi2_contingency(pd.crosstab(x, y))           # independence
stats.pearsonr(x, y); stats.spearmanr(x, y)
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep
proportions_ztest([x1, x2], [n1, n2])
import statsmodels.formula.api as smf
smf.ols("y ~ x1 + C(cat)", data=df).fit().summary()
smf.logit("churn ~ logins + C(plan)", data=df).fit().summary()
```
""",
    "scikit-learn": """
```python
from sklearn.model_selection import train_test_split, StratifiedKFold, TimeSeriesSplit, cross_val_score, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
pre = ColumnTransformer([("num", StandardScaler(), num), ("cat", OneHotEncoder(handle_unknown="ignore"), cat)])
model = Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=1000))])
cross_val_score(model, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0), scoring="roc_auc")
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score
from sklearn.inspection import permutation_importance
```
""",
    "Optimisation (SciPy)": """
```python
from scipy.optimize import linprog, milp, LinearConstraint, Bounds, linear_sum_assignment
# maximise c @ x  ->  minimise -c @ x
res = linprog(-c, A_ub=A, b_ub=b, A_eq=Aeq, b_eq=beq, bounds=[(lo, hi), ...], method="highs")
res.x, -res.fun, res.slack, res.ineqlin.marginals   # duals for the minimisation
rows, cols = linear_sum_assignment(cost)            # assignment
milp(c, constraints=LinearConstraint(A, lb, ub), integrality=np.ones(n), bounds=Bounds(0, ub))
rng = np.random.default_rng(42); rng.normal(mu, sd, n); rng.triangular(lo, mode, hi, n)
```
""",
    "Matplotlib": """
```python
fig, ax = plt.subplots(figsize=(9, 4))               # or plt.subplots(2, 2, sharey=True)
ax.plot(x, y); ax.bar(cats, vals); ax.barh(cats, vals); ax.scatter(x, y, alpha=.3); ax.hist(v, bins=30)
ax.errorbar(x, y, yerr=e, fmt="o", capsize=4); ax.fill_between(x, lo, hi, alpha=.2)
ax.set_title("Finding as a sentence"); ax.set_xlabel("Month"); ax.set_ylabel("Revenue (EUR)")
ax.set_ylim(bottom=0); ax.set_yscale("log")
ax.annotate("Event", xy=(x0, y0), xytext=(x1, y1), arrowprops=dict(arrowstyle="->"))
ax.bar_label(bars, fmt="%.0f"); ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout()
import matplotlib.ticker as mtick; ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
```
""",
    "Excel": """
| Need | Formula |
|---|---|
| Absolute reference | `=B2*$H$1` (F4 toggles) |
| Conditional sum | `=SUMIFS(Rev, Region, "West", Date, ">="&DATE(2024,1,1))` |
| Conditional count / average | `=COUNTIFS(...)`, `=AVERAGEIFS(...)` |
| Lookup | `=XLOOKUP(key, Keys, Values, "not found")` or `=INDEX(Values, MATCH(key, Keys, 0))` |
| Logic | `=IF(x>0,"Yes","No")`, `=IFS(x>=500,"A",x>=100,"B",TRUE,"C")`, `=IFERROR(x, 0)` |
| Text / dates | `TRIM`, `PROPER`, `LEFT`, `TEXT(d,"yyyy-mm")`, `EOMONTH`, `YEAR`, `NETWORKDAYS` |
| Tables | Ctrl+T, structured references `Sales[Revenue]`, `[@Revenue]` |
| What-if | Data -> What-If Analysis -> Data Table / Goal Seek / Scenario Manager |
| Audit | Formulas -> Trace Precedents / Evaluate Formula; separate Inputs / Calc / Output / Checks sheets |
""",
    "Power BI / DAX": """
```DAX
Revenue      = SUMX(order_items, order_items[quantity] * order_items[unit_price] * (1 - order_items[discount_pct]))
Orders       = DISTINCTCOUNT(orders[order_id])
AOV          = DIVIDE([Revenue], [Orders])
Margin %     = DIVIDE([Revenue] - [Cost], [Revenue])
Revenue YTD  = TOTALYTD([Revenue], 'Calendar'[Date])
Revenue PY   = CALCULATE([Revenue], SAMEPERIODLASTYEAR('Calendar'[Date]))
Share of all = DIVIDE([Revenue], CALCULATE([Revenue], ALL(products[category])))
```
Model: star schema, one-to-many single-direction relationships, marked Calendar table, measures over calculated columns, hide foreign keys.
""",
    "R": """
```r
df <- read.csv("file.csv"); str(df); summary(df); head(df)
df[df$status == "Completed", c("a", "b")]
mean(x, na.rm = TRUE); table(a, b); prop.table(table(a))
aggregate(y ~ g, data = df, FUN = mean); tapply(df$y, df$g, mean)
merge(a, b, by = "key", all.x = TRUE)
t.test(y ~ g, data = df); chisq.test(table(a, b)); prop.test(c(k1, k2), c(n1, n2)); cor.test(x, y, method = "spearman")
fit <- lm(y ~ x1 + x2, data = df); summary(fit); predict(fit, newdata = test)
glm(churn ~ logins, family = binomial, data = df)
# tidyverse
library(dplyr); df |> filter(x > 0) |> group_by(g) |> summarise(n = n(), m = mean(y)) |> arrange(desc(m))
library(ggplot2); ggplot(df, aes(x, y, colour = g)) + geom_point() + labs(title = "...", x = "...", y = "...")
```
""",
    "Tableau": """
* Dimensions (blue = discrete) create headers; measures (green = continuous) create axes.
* `ZN([x])` NULL -> 0; `IF ... THEN ... ELSEIF ... END`; `DATETRUNC('month', [Order Date])`.
* LOD: `{ FIXED [Customer Id] : MIN([Order Date]) }`, `{ INCLUDE ... }`, `{ EXCLUDE ... }`.
* Table calcs: `RUNNING_SUM(SUM([Revenue]))`, `WINDOW_AVG(...)`, `RANK(...)` - computed on the view.
* Filters order: extract -> data source -> context -> dimension -> measure -> table calc.
* Dashboard actions: filter, highlight, URL, parameter actions.
""",
    "Looker Studio": """
* One flat, tidy table per data source works best; set field types (Date, Number, Currency) and default aggregation.
* Calculated fields: `SUM(revenue) / COUNT_DISTINCT(order_id)`, `CASE WHEN ... THEN ... ELSE ... END`.
* Scorecards with comparison date range; time series with date granularity; controls (date range, drop-down).
* Blending joins data sources on shared dimensions - check the grain.
* Share as viewer; document definitions in a text box.
""",
}


def search_reference(term: str) -> list[tuple[str, str, str]]:
    """Return (kind, title, text) matches across glossary and cheat sheets."""
    t = term.lower().strip()
    if not t:
        return []
    out = [("Glossary", k, v) for k, v in GLOSSARY.items() if t in k.lower() or t in v.lower()]
    out += [("Cheat sheet", k, v) for k, v in CHEATSHEETS.items() if t in k.lower() or t in v.lower()]
    return out
