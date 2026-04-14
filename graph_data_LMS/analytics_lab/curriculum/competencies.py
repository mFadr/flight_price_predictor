"""Transparent competency model. Every lesson, question and exercise is tagged
with one or more of these ids, and mastery is computed from the evidence."""

from analytics_lab.models import Competency

COMPETENCIES: list[Competency] = [
    # Descriptive
    Competency("sql_basics", "SQL querying fundamentals", "descriptive", "Select, filter, sort and aggregate rows correctly.", foundational=True),
    Competency("sql_aggregation", "Aggregation & conditional logic", "descriptive", "GROUP BY/HAVING, CASE and NULL handling for business summaries.", requires_practical=True),
    Competency("sql_joins", "Joins, CTEs & subqueries", "descriptive", "Combine tables without duplicating or losing rows; structure multi-step queries.", requires_practical=True),
    Competency("sql_window", "Window functions & time comparisons", "descriptive", "Rankings, running totals, period-over-period comparisons.", requires_practical=True),
    Competency("excel_analysis", "Spreadsheet analysis", "descriptive", "Formulas, lookups, PivotTables and auditable workbook design."),
    Competency("bi_modeling", "BI data modelling & DAX", "descriptive", "Star schemas, relationships, measures and filter context."),
    Competency("kpi_reporting", "KPI design & reporting", "descriptive", "Define, compute and interpret business KPIs.", foundational=True),
    # Diagnostic
    Competency("data_quality", "Data quality & EDA", "diagnostic", "Detect missing values, duplicates, outliers and inconsistent records.", foundational=True),
    Competency("segmentation_rca", "Segmentation & root-cause analysis", "diagnostic", "Decompose KPI changes and compare segments to localise causes.", requires_practical=True),
    Competency("cohort_funnel", "Cohort, retention & funnel analysis", "diagnostic", "Build cohort tables, retention curves and funnels.", requires_practical=True),
    Competency("statistical_inference", "Statistical inference & A/B testing", "diagnostic", "Hypothesis tests, confidence intervals, practical significance.", requires_practical=True),
    Competency("causal_reasoning", "Causal reasoning", "diagnostic", "Confounding, Simpson's paradox, correlation vs causation.", foundational=True),
    Competency("r_programming", "R for analysis", "diagnostic", "Data frames, grouping and statistical tests in R."),
    # Predictive
    Competency("ml_framing", "Prediction framing & leakage", "predictive", "Define targets, splits and baselines; prevent leakage.", foundational=True),
    Competency("regression_modeling", "Regression modelling", "predictive", "Fit and evaluate regression models with MAE/RMSE/R².", requires_practical=True),
    Competency("classification_modeling", "Classification & thresholds", "predictive", "Classifiers, confusion matrices, precision/recall, thresholds.", requires_practical=True),
    Competency("model_validation", "Validation, tuning & pipelines", "predictive", "Cross-validation, pipelines, tuning and over/underfitting.", requires_practical=True),
    Competency("forecasting", "Time-series forecasting", "predictive", "Temporal splits, seasonal baselines and forecast accuracy.", requires_practical=True),
    Competency("responsible_ml", "Interpretation & responsible use", "predictive", "Feature importance, uncertainty, drift and fairness."),
    # Prescriptive
    Competency("optimization_modeling", "Optimisation modelling", "prescriptive", "Decision variables, objectives, constraints and LP solving.", requires_practical=True),
    Competency("simulation_risk", "Simulation & risk", "prescriptive", "Monte Carlo simulation and risk-aware decisions.", requires_practical=True),
    Competency("decision_analysis", "Decision & sensitivity analysis", "prescriptive", "Scenarios, sensitivity, cost-benefit and recommendations.", foundational=True),
    # Visualization
    Competency("chart_selection", "Chart selection", "visualization", "Match chart types to analytical questions and audiences.", foundational=True),
    Competency("viz_coding", "Visualisation coding (Matplotlib)", "visualization", "Produce correct, labelled charts in code.", requires_practical=True),
    Competency("viz_integrity", "Design & integrity", "visualization", "Accessible, honest, uncluttered visual design."),
    Competency("storytelling", "Dashboards & storytelling", "visualization", "Dashboards, executive summaries and communicating uncertainty."),
]

BY_ID = {c.id: c for c in COMPETENCIES}


def for_module(module: str) -> list[Competency]:
    return [c for c in COMPETENCIES if c.module == module]
