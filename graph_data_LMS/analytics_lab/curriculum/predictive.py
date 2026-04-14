"""Module 3 - Predictive Analytics (Python, R)."""

from analytics_lab.models import Lesson, WorkedExample

LESSONS = [
    Lesson(
        id="pr1",
        module="predictive",
        level="Beginner",
        title="Framing prediction problems: targets, splits, baselines and leakage",
        tools=["Python"],
        minutes=45,
        competencies=["ml_framing"],
        objectives=[
            "Distinguish prediction from inference.",
            "Define a prediction target, prediction time and decision it supports.",
            "Split data into train/validation/test correctly, including temporal splits.",
            "Build a baseline and recognise target and temporal leakage.",
        ],
        concept="""
**Prediction vs inference.** *Inference* asks how and why variables relate (is price associated with churn, controlling for plan?). *Prediction* asks how accurately we can forecast an outcome for new cases. A model can predict well without being causally interpretable - and vice versa.

**Frame the problem before modelling:**

| Question | Example (CloudNest churn) |
|---|---|
| Decision supported | Which new customers should Customer Success call in month 2? |
| Target | `churned_6m` = cancelled within 182 days of signup |
| Prediction time | End of the first month after signup |
| Allowed features | Only information available at prediction time |
| Cost of errors | Missed churner = lost revenue; wasted call = ~EUR 15 |

**Splits.** *Train* to fit, *validation* to choose models and hyperparameters, *test* to estimate final performance once. When rows are ordered in time and you will predict the future, split by **time** (train on older sign-ups, test on newer ones). A random split lets the model learn from the future.

**Baselines.** Always compare with a trivial model: the majority class (classification), the training mean (regression) or last value / same period last week (forecasting). A model is only useful if it beats the baseline by a margin that matters.

**Leakage** is information in training that will not be available at prediction time:

* *Target leakage* - features caused by the target (`cancellation_reason` is only filled in after a customer cancels).
* *Temporal leakage* - features computed with future data (e.g. "total tickets ever" for a customer at month 1).
* *Train-test contamination* - fitting scalers/encoders on all data before splitting.

Suspiciously high accuracy is a leakage alarm, not a celebration.
""",
        business_context="""
CloudNest's Customer Success team can call about 30% of new customers. They want a churn-risk score at the end of each customer's first month. Before any modelling you must define the target, the split and the baseline the model must beat.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"cf": "subscription.churn_features"},
            code="""# Temporal split: train on earlier sign-ups, test on later ones
train = cf[cf.signup_date < "2024-04-01"]
test = cf[cf.signup_date >= "2024-04-01"]
print(f"train: {len(train)} rows, churn {train.churned_6m.mean():.1%}")
print(f"test:  {len(test)} rows, churn {test.churned_6m.mean():.1%}")

# Majority-class baseline: predict 'no churn' for everyone
majority = int(train.churned_6m.mean() >= 0.5)
acc = (test.churned_6m == majority).mean()
print(f"baseline accuracy {acc:.1%} - but it finds 0% of churners")

# Leakage check: which columns are only known after the outcome?
print(cf.groupby(cf.cancellation_reason.isna()).churned_6m.mean())""",
            explanation="""
* Churn is higher in the test period (the acquisition mix shifted) - a temporal split reveals this **distribution shift**; a random split would hide it.
* The majority baseline has ~68% accuracy yet is useless for the business: accuracy is the wrong metric when classes are imbalanced and the minority class matters.
* `cancellation_reason` is missing exactly when the customer did not churn: it perfectly encodes the target and must be excluded.
""",
        ),
        knowledge_check=["q_pr_001", "q_pr_002", "q_pr_003"],
        guided_exercise="ex_py_pr1_baseline",
        challenge=None,
        summary=[
            "Define decision, target, prediction time and allowed features first.",
            "Split by time when predicting the future; touch the test set once.",
            "Every model must beat a simple baseline on a metric that matters.",
            "Leakage produces great offline scores and useless production models.",
        ],
        common_mistakes=[
            "Random splits for time-ordered problems.",
            "Using accuracy on imbalanced classes.",
            "Including post-outcome fields as features.",
        ],
        revision="List every column in churn_features and mark when it becomes known.",
        next_lesson="pr2",
        order=15,
    ),
    Lesson(
        id="pr2",
        module="predictive",
        level="Intermediate",
        title="Regression models and error metrics",
        tools=["Python", "R"],
        minutes=45,
        competencies=["regression_modeling", "ml_framing"],
        objectives=[
            "Fit a linear regression and interpret coefficients.",
            "Evaluate with MAE, RMSE and R-squared on held-out data.",
            "Choose a metric that matches the business cost of errors.",
            "Diagnose non-linearity and use transformations.",
        ],
        concept="""
**Linear regression** models y = b0 + b1*x1 + ... + e and chooses coefficients that minimise squared error. b1 is the expected change in y for a one-unit change in x1, *holding other features constant* - an associational statement, not a causal one, unless the data come from an experiment.

**Metrics (always on held-out data):**

| Metric | Formula | Use when |
|---|---|---|
| MAE | mean(abs(y - yhat)) | errors cost proportionally; easy to explain ("off by EUR 3k on average") |
| RMSE | sqrt(mean((y - yhat)^2)) | large errors are disproportionately bad |
| R-squared | 1 - SSE/SST | share of variance explained relative to predicting the mean; can be negative on test data |
| MAPE | mean(abs(error / y)) | relative error; breaks when y is near 0 |

R-squared depends on the variance of y in the test set; compare MAE/RMSE with a baseline (e.g. predicting the training mean) instead of chasing a high R-squared.

**Non-linearity.** Marketing response has diminishing returns: each extra euro brings less revenue. A log-log model `log(revenue) = a + b*log(spend)` captures this; b is an *elasticity* (a 1% spend increase -> b% revenue increase). Residual plots (residuals vs fitted) reveal curvature and heteroscedasticity.

**R equivalent:**

```r
fit <- lm(revenue ~ spend, data = train)
summary(fit)                     # coefficients, R-squared, p-values
pred <- predict(fit, newdata = test)
mae <- mean(abs(test$revenue - pred))
```
""",
        business_context="""
The marketing team wants to predict weekly Search revenue from planned spend to support next quarter's budget. Using two years of weekly data, you fit a model on the first 78 weeks and test it on the last 26.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"cp": "marketing.channel_performance"},
            code="""from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

s = cp[cp.channel == "Search"].sort_values("week_start").reset_index(drop=True)
train, test = s.iloc[:78], s.iloc[78:]

lin = LinearRegression().fit(train[["spend"]], train.revenue)
pred = lin.predict(test[["spend"]])

loglog = LinearRegression().fit(np.log(train[["spend"]]), np.log(train.revenue))
pred_log = np.exp(loglog.predict(np.log(test[["spend"]])))

base = np.full(len(test), train.revenue.mean())
for name, p in [("baseline (train mean)", base), ("linear", pred), ("log-log", pred_log)]:
    print(f"{name:22s} MAE={mean_absolute_error(test.revenue, p):8.0f}  "
          f"RMSE={mean_squared_error(test.revenue, p) ** 0.5:8.0f}  R2={r2_score(test.revenue, p):.3f}")
print(f"slope: {lin.coef_[0]:.2f} revenue per EUR; elasticity: {loglog.coef_[0]:.2f}")""",
            explanation="""
* Both models clearly beat the mean baseline - spend carries real signal.
* The elasticity below 1 confirms **diminishing returns**: doubling spend increases revenue by less than double. This matters for budget allocation (Module 4).
* The linear slope is an *average* return over the observed spend range; extrapolating far beyond it is risky.
""",
        ),
        knowledge_check=["q_pr_004", "q_pr_005", "q_pr_006"],
        guided_exercise="ex_py_pr2_regression",
        challenge="ex_r_pr2_lm",
        summary=[
            "Coefficients describe associations holding other features constant.",
            "Evaluate MAE/RMSE on held-out data against a baseline.",
            "Pick metrics that reflect the business cost of errors.",
            "Use transformations (log-log) for diminishing returns; avoid extrapolation.",
        ],
        common_mistakes=[
            "Reporting training R-squared as model quality.",
            "Interpreting coefficients causally from observational data.",
            "Using MAPE when actuals can be close to zero.",
        ],
        revision="Plot residuals vs fitted values for the linear model and describe the pattern.",
        next_lesson="pr3",
        order=16,
    ),
    Lesson(
        id="pr3",
        module="predictive",
        level="Intermediate",
        title="Classification, confusion matrices and thresholds",
        tools=["Python"],
        minutes=50,
        competencies=["classification_modeling", "ml_framing"],
        objectives=[
            "Fit a logistic regression classifier.",
            "Read a confusion matrix and compute precision, recall and F1.",
            "Compare ROC-AUC and PR-AUC, especially with class imbalance.",
            "Choose a decision threshold from business costs and capacity.",
        ],
        concept="""
**Logistic regression** predicts a probability p = 1 / (1 + e^-(b0 + b1x1 + ...)). Coefficients are changes in **log-odds**.

**Confusion matrix** at a threshold t (predict churn if p >= t):

|  | Predicted churn | Predicted stay |
|---|---|---|
| **Actual churn** | TP | FN |
| **Actual stay** | FP | TN |

* **Precision** = TP / (TP + FP): of the customers we call, how many would have churned?
* **Recall** = TP / (TP + FN): of all churners, how many did we reach?
* **F1** = harmonic mean of precision and recall.
* **Accuracy** = (TP + TN) / all - misleading with imbalance.

**Threshold choice is a business decision.** Lowering the threshold increases recall and lowers precision. Choose it from costs and capacity: e.g. if a call costs EUR 15 and saves 20% of churners worth EUR 300, calling is worth it when p x 0.2 x 300 > 15, i.e. p > 0.25. If the team can only call 30% of customers, pick the threshold that flags 30%.

**Ranking metrics (threshold-free):**

* **ROC-AUC** - probability that a random churner is scored higher than a random non-churner. 0.5 = random.
* **PR-AUC** (average precision) - focuses on the positive class; more informative under strong imbalance. Its baseline is the positive rate, not 0.5.

**Class imbalance:** use stratified splits, appropriate metrics, `class_weight="balanced"` or resampling - and remember that reweighting changes probability calibration.
""",
        business_context="""
Customer Success can call roughly 30% of new customers. You need a churn model and a threshold, and you must explain what precision and recall mean in terms of calls made and churners reached.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"cf": "subscription.churn_features"},
            code="""from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import confusion_matrix, precision_score, recall_score, roc_auc_score, average_precision_score

num = ["logins_first_month", "features_first_month", "minutes_first_month", "tickets_first_30d"]
X = pd.get_dummies(cf[num + ["plan", "acquisition_source"]], columns=["plan", "acquisition_source"], dtype=float).fillna(0)
y = cf.churned_6m
is_test = cf.signup_date >= "2024-04-01"

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
model.fit(X[~is_test], y[~is_test])
p = model.predict_proba(X[is_test])[:, 1]

print(f"ROC-AUC {roc_auc_score(y[is_test], p):.3f}   PR-AUC {average_precision_score(y[is_test], p):.3f}   (positive rate {y[is_test].mean():.3f})")
for t in [0.5, 0.35, 0.25]:
    pred = (p >= t).astype(int)
    print(f"t={t}: flagged {pred.mean():.0%}  precision {precision_score(y[is_test], pred):.2f}  recall {recall_score(y[is_test], pred):.2f}")
print(confusion_matrix(y[is_test], (p >= 0.35).astype(int)))""",
            explanation="""
* The scaler is inside the pipeline, so it is fitted on training data only (no contamination).
* At t = 0.5 the model flags few customers: high precision, low recall. Lowering t trades precision for recall.
* Pick the threshold whose *flagged share* matches the team's 30% capacity, then report expected precision ("about X of every 10 calls reach a real churn risk") and recall.
""",
        ),
        knowledge_check=["q_pr_007", "q_pr_008", "q_pr_009", "q_pr_010"],
        guided_exercise="ex_py_pr3_threshold",
        challenge=None,
        summary=[
            "Precision = quality of the flagged list; recall = coverage of actual positives.",
            "Thresholds should come from costs, benefits and capacity, not 0.5 by default.",
            "ROC-AUC measures ranking; PR-AUC is more informative under imbalance.",
            "Keep preprocessing inside pipelines to avoid contamination.",
        ],
        common_mistakes=[
            "Reporting accuracy for an imbalanced problem.",
            "Using the default 0.5 threshold without justification.",
            "Comparing PR-AUC to 0.5 instead of the positive rate.",
        ],
        revision="Compute expected net value of calling at three thresholds using the cost figures above.",
        next_lesson="pr4",
        order=17,
    ),
    Lesson(
        id="pr4",
        module="predictive",
        level="Advanced",
        title="Trees, forests, pipelines and cross-validation",
        tools=["Python", "R"],
        minutes=55,
        competencies=["model_validation", "classification_modeling"],
        objectives=[
            "Explain decision trees and random forests and their trade-offs.",
            "Build preprocessing + model pipelines with ColumnTransformer.",
            "Estimate performance with k-fold cross-validation.",
            "Tune hyperparameters without overfitting the validation data.",
        ],
        concept="""
**Decision trees** split data with if/then rules that best separate the target. They capture non-linearities and interactions and need little preprocessing, but a deep tree memorises noise (**overfitting**).

**Random forests** average many trees trained on bootstrap samples with random feature subsets. Averaging reduces variance, so forests usually generalise much better than single trees. Gradient boosting (e.g. `HistGradientBoostingClassifier`) builds trees sequentially and is often stronger still.

**Bias-variance trade-off.** *Underfitting* (high bias): poor on both train and test. *Overfitting* (high variance): great on train, poor on test. Learning curves and the train-validation gap diagnose which you have.

**Pipelines** chain preprocessing and the model so that every transformation is learned from the training fold only:

```python
pre = ColumnTransformer([
    ("num", StandardScaler(), numeric_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
])
model = Pipeline([("pre", pre), ("clf", RandomForestClassifier(random_state=0))])
```

**Cross-validation** splits the training data into k folds, trains k times and averages the scores - a more stable estimate than one validation split. Use `StratifiedKFold` for classification; use `TimeSeriesSplit` for temporal data.

**Hyperparameter tuning** (`GridSearchCV`, `RandomizedSearchCV`) selects settings by CV score. The chosen model's CV score is optimistically biased; confirm on an untouched test set. Simpler models within noise of the best are often preferable (easier to explain and maintain).

**R equivalents:** `rpart` (trees), `randomForest` or `ranger` (forests), `caret` / `tidymodels` (pipelines and CV).
""",
        business_context="""
The data science lead asks: "Is a random forest worth its extra complexity over logistic regression for churn?" You must answer with a fair comparison - same features, same folds, same metric.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"cf": "subscription.churn_features"},
            code="""from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate

num = ["logins_first_month", "features_first_month", "minutes_first_month", "tickets_first_30d", "avg_satisfaction_first_30d"]
cat = ["plan", "acquisition_source", "company_size", "region"]
train = cf[cf.signup_date < "2024-04-01"]
pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
])
cv = StratifiedKFold(5, shuffle=True, random_state=0)
models = {
    "logistic": LogisticRegression(max_iter=1000),
    "deep tree": DecisionTreeClassifier(random_state=0),
    "forest": RandomForestClassifier(n_estimators=150, min_samples_leaf=20, random_state=0, n_jobs=1),
}
for name, clf in models.items():
    r = cross_validate(Pipeline([("pre", pre), ("clf", clf)]), train[num + cat], train.churned_6m,
                       cv=cv, scoring="roc_auc", return_train_score=True)
    print(f"{name:10s} train AUC {r['train_score'].mean():.3f}  CV AUC {r['test_score'].mean():.3f} +/- {r['test_score'].std():.3f}")""",
            explanation="""
* The unpruned tree scores ~1.0 on training folds but far lower on validation folds: textbook overfitting.
* The forest and logistic regression perform similarly in CV. When a complex model does not clearly beat a simple one, prefer the simpler, more explainable model.
* `SimpleImputer` handles missing satisfaction scores inside the pipeline, so imputation values are learned per training fold.
""",
        ),
        knowledge_check=["q_pr_011", "q_pr_012", "q_pr_013"],
        guided_exercise="ex_py_pr4_cv",
        challenge=None,
        summary=[
            "Trees capture non-linearity but overfit; forests average away variance.",
            "Pipelines prevent leakage from preprocessing.",
            "Cross-validation gives stable estimates; use stratified or time-series folds as appropriate.",
            "Prefer simpler models when performance differences are within noise.",
        ],
        common_mistakes=[
            "Fitting scalers or encoders before splitting.",
            "Reporting the best CV score after heavy tuning as expected production performance.",
            "Comparing models on different folds or features.",
        ],
        revision="Add a HistGradientBoostingClassifier to the comparison and interpret the result.",
        next_lesson="pr5",
        order=18,
    ),
    Lesson(
        id="pr5",
        module="predictive",
        level="Advanced",
        title="Time-series forecasting fundamentals",
        tools=["Python", "R"],
        minutes=50,
        competencies=["forecasting", "ml_framing"],
        objectives=[
            "Describe trend, seasonality and noise in a time series.",
            "Evaluate forecasts with temporal holdouts and rolling origins.",
            "Build naive and seasonal-naive baselines.",
            "Fit exponential smoothing and communicate forecast uncertainty.",
        ],
        concept="""
A time series combines **trend** (long-term direction), **seasonality** (repeating patterns - weekly, yearly) and **noise**. Plot the series and its seasonal profile before modelling.

**Evaluation must respect time.** Hold out the most recent period (e.g. last 28 days) as the test set. Better: *rolling-origin* evaluation - forecast from several cut-off dates and average the errors. Never shuffle.

**Baselines you must beat:**

* *Naive:* tomorrow = today.
* *Seasonal naive:* next Monday = last Monday (for daily data with weekly seasonality).
* *Moving average:* mean of the last k periods.

**Exponential smoothing (ETS / Holt-Winters)** weights recent observations more heavily and can model level, trend and seasonality:

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing
fit = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=7).fit()
forecast = fit.forecast(28)
```

**Regression with calendar features** (day of week, month, promotions, holidays) is a flexible alternative; lagged features must only use information available at forecast time.

**Uncertainty.** Point forecasts are always wrong; communicate prediction intervals (e.g. 80% range) or quantiles. For inventory decisions the *upper* quantile often matters more than the mean.

**Censored demand.** If sales are capped by stock-outs, forecasting *sales* underestimates *demand*.

**R equivalents:** `forecast::ets()`, `forecast::snaive()`, `fable` (tidy forecasting).
""",
        business_context="""
Meridian Supply's planners need a 4-week daily forecast of total demand to staff the warehouse. You must show that your method beats simple baselines on the most recent four weeks.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"dd": "operations.daily_demand"},
            code="""from statsmodels.tsa.holtwinters import ExponentialSmoothing

y = dd.groupby("date").units_demanded.sum().asfreq("D")
train, test = y.iloc[:-28], y.iloc[-28:]

naive = np.repeat(train.iloc[-1], 28)
snaive = np.tile(train.iloc[-7:].values, 4)
hw = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=7).fit().forecast(28)

mae = lambda p: np.mean(np.abs(test.values - np.asarray(p)))
print(f"naive MAE          {mae(naive):7.1f}")
print(f"seasonal naive MAE {mae(snaive):7.1f}")
print(f"Holt-Winters MAE   {mae(hw):7.1f}")
print(test.groupby(test.index.dayofweek).mean().round(0))  # weekday profile""",
            explanation="""
* Weekly seasonality is strong (weekends are much lower), so the naive forecast is poor and the seasonal naive baseline is much better.
* Holt-Winters should be judged against seasonal naive, not against naive. If it does not beat seasonal naive meaningfully, its complexity is not justified.
* For staffing, report a range: e.g. the 80% interval from simulated or residual-based errors.
""",
        ),
        knowledge_check=["q_pr_014", "q_pr_015", "q_pr_016"],
        guided_exercise="ex_py_pr5_forecast",
        challenge=None,
        summary=[
            "Decompose series into trend, seasonality and noise.",
            "Use temporal holdouts or rolling origins - never random splits.",
            "Seasonal naive is the baseline to beat for seasonal data.",
            "Communicate forecast intervals, not just point forecasts.",
        ],
        common_mistakes=[
            "Comparing a seasonal model only with a non-seasonal baseline.",
            "Using future information in lag features.",
            "Forecasting sales instead of demand when stock-outs occurred.",
        ],
        revision="Repeat the evaluation with three different cut-off dates (rolling origin).",
        next_lesson="pr6",
        order=19,
    ),
    Lesson(
        id="pr6",
        module="predictive",
        level="Professional",
        title="Interpretation, uncertainty, drift and responsible use",
        tools=["Python"],
        minutes=45,
        competencies=["responsible_ml", "ml_framing"],
        objectives=[
            "Interpret models with permutation importance and partial dependence.",
            "Detect leakage through suspicious importance and performance.",
            "Monitor data and concept drift after deployment.",
            "Assess fairness, uncertainty and whether a model is useful in practice.",
        ],
        concept="""
**Interpretation tools**

* *Coefficients* (linear/logistic) - direction and size of association, after scaling.
* *Permutation importance* - drop in a metric when one feature is shuffled on held-out data. Model-agnostic; correlated features share importance.
* *Partial dependence / ICE plots* - how predictions change as one feature varies.
* *SHAP values* - per-prediction attributions (optional `shap` package).

Importance shows what the model **uses**, not what **causes** the outcome.

**Leakage detection.** If one feature dominates importance and test AUC is near 1.0, ask: *could we know this value at prediction time?*

**Is the model useful?** Compare against the baseline and the current business process; translate metrics into value (calls saved, stock-outs avoided); consider the cost of maintaining it.

**Uncertainty.** Report CV spread or bootstrap intervals for metrics; check calibration (do predicted 30% risks churn ~30% of the time?).

**Drift and monitoring**

* *Data drift* - input distributions change (more Paid Social customers).
* *Concept drift* - the relationship between inputs and outcome changes (a price rise changes who churns).
* Monitor input distributions, prediction distributions and realised performance once labels arrive; set retraining triggers.

**Responsible use.** Check performance across groups (regions, company sizes); avoid proxies for protected attributes; document intended use and limitations in a *model card*; keep a human in the loop for consequential decisions.
""",
        business_context="""
A junior analyst proudly reports a churn model with AUC 0.99. Your manager asks you to review it before it goes to Customer Success - and to write the monitoring plan for the model that eventually ships.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"cf": "subscription.churn_features"},
            code="""from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score

num = ["logins_first_month", "features_first_month", "minutes_first_month", "tickets_first_30d"]
X = pd.get_dummies(cf[num + ["plan", "acquisition_source", "cancellation_reason"]].fillna({"cancellation_reason": "none"}),
                   columns=["plan", "acquisition_source", "cancellation_reason"], dtype=float).fillna(0)
y = cf.churned_6m
test = cf.signup_date >= "2024-04-01"
rf = RandomForestClassifier(n_estimators=100, min_samples_leaf=20, random_state=0, n_jobs=1).fit(X[~test], y[~test])
print("test AUC with all columns:", round(roc_auc_score(y[test], rf.predict_proba(X[test])[:, 1]), 3))

imp = permutation_importance(rf, X[test], y[test], scoring="roc_auc", n_repeats=3, random_state=0)
print(pd.Series(imp.importances_mean, index=X.columns).sort_values(ascending=False).head(6).round(3))

# Data drift: compare the input mix between training and test periods
print(pd.crosstab(test, cf.acquisition_source, normalize="index").round(2))""",
            explanation="""
* AUC near 1.0 and `cancellation_reason_none` dominating importance = **target leakage**. Remove the column and retrain; expect a much lower but honest AUC.
* The crosstab shows **data drift**: Paid Social's share more than doubles in the test period. A model trained on 2023 customers will face a different population - monitor it.
""",
        ),
        knowledge_check=["q_pr_017", "q_pr_018", "q_pr_019", "q_pr_020"],
        guided_exercise="ex_py_pr6_leakage",
        challenge=None,
        summary=[
            "Importance explains model behaviour, not causation.",
            "A dominant feature plus near-perfect scores signals leakage.",
            "Monitor data drift, concept drift and realised performance.",
            "Check calibration, subgroup performance and document limitations in a model card.",
        ],
        common_mistakes=[
            "Celebrating AUC 0.99 without checking feature availability.",
            "Deploying without monitoring or retraining triggers.",
            "Assuming one global metric means the model works equally well for all groups.",
        ],
        revision="Write a one-page model card for the clean churn model, then start Capstone 3.",
        next_lesson="ps1",
        order=20,
    ),
]
