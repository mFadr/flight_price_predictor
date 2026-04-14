"""Scoring of multiple-choice, SQL result sets, Python and R exercises."""

import pandas as pd
import pytest

from analytics_lab.assessment.bank import EXERCISES_BY_ID, QUESTIONS_BY_ID
from analytics_lab.assessment.grading import compare_result_sets, grade_exercise, grade_mcq
from analytics_lab.execution.runners import RunSettings

EXPECTED = pd.DataFrame({"region": ["East", "West"], "revenue": [100.0, 50.0]})


def score_of(user, **kw):
    items, score = compare_result_sets(user, EXPECTED, **kw)
    return score, {i.name: i.passed for i in items}


def test_exact_match_full_score():
    assert score_of(EXPECTED.copy())[0] == 100


def test_column_names_case_insensitive_and_float_tolerance():
    user = pd.DataFrame({"REGION": ["East", "West"], "Revenue": [100.004, 49.996]})
    assert score_of(user)[0] == 100


def test_row_order_ignored_unless_required():
    user = EXPECTED.iloc[::-1].reset_index(drop=True)
    assert score_of(user)[0] == 100
    s, items = score_of(user, order_matters=True)
    assert s < 100 and items["Ordering"] is False and items["Values"] is True


def test_wrong_values_partial_credit_with_message():
    user = pd.DataFrame({"region": ["East", "West"], "revenue": [100.0, 75.0]})
    items, score = compare_result_sets(user, EXPECTED)
    assert 0 < score < 100
    values = next(i for i in items if i.name == "Values")
    assert not values.passed and "revenue" in values.message


def test_wrong_row_count():
    s, items = score_of(EXPECTED.head(1))
    assert items["Row count"] is False and s <= 40


def test_column_alias_mismatch_compared_by_position():
    user = EXPECTED.rename(columns={"revenue": "total"})
    s, items = score_of(user)
    assert items["Columns"] is False and items["Values"] is True and s < 100


def test_date_normalisation():
    e = pd.DataFrame({"month": ["2024-01-01"]})
    u = pd.DataFrame({"month": ["2024-01-01T00:00:00"]})
    assert compare_result_sets(u, e)[1] == 100


def test_mcq_single_and_multi():
    q = QUESTIONS_BY_ID["q_ds_002"]
    right = next(iter(q.correct_keys))
    assert grade_mcq(q, [right]).correct
    assert not grade_mcq(q, [(right + 1) % 4]).correct
    multi = QUESTIONS_BY_ID["q_ds_005"]
    keys = sorted(multi.correct_keys)
    assert multi.qtype == "multi"
    assert grade_mcq(multi, keys).correct
    partial = grade_mcq(multi, keys[:1])
    assert not partial.correct and 0 < partial.partial < 1


def test_sql_exercise_equivalent_query_passes():
    ex = EXERCISES_BY_ID["ex_sql_ds2_loyal_customers"]
    alt = ("WITH c AS (SELECT customer_id, order_date FROM orders WHERE status = 'Completed') "
           "SELECT customer_id, COUNT(*) completed_orders, MIN(order_date) first_order, MAX(order_date) last_order "
           "FROM c GROUP BY ALL HAVING COUNT(*) >= 16 ORDER BY 2 DESC, 1")
    assert grade_exercise(ex, alt).passed


def test_sql_exercise_missing_filter_fails():
    ex = EXERCISES_BY_ID["ex_sql_ds1_top_products"]
    g = grade_exercise(ex, "SELECT product_id, product_name, unit_price, unit_cost FROM products WHERE category_id = 4 ORDER BY unit_price DESC LIMIT 10")
    assert not g.passed and g.next_step


def test_sql_exercise_syntax_error_feedback():
    g = grade_exercise(EXERCISES_BY_ID["ex_sql_ds1_headline"], "SELEC COUNT(*) FROM orders")
    assert g.score == 0 and g.error


def test_python_exercise_partial_credit():
    ex = EXERCISES_BY_ID["ex_py_dg1_quality"]
    code = "missing_birth_year = int(customers['birth_year'].isna().sum())\nmissing_birth_year_pct = 0\nunique_people = 0\nduplicate_records = 0\ndupes = customers.head(0)"
    g = grade_exercise(ex, code)
    assert not g.passed and 0 < g.score < 100
    assert any(i.passed for i in g.items) and any(not i.passed for i in g.items)


def test_python_exercise_leakage_detected():
    ex = EXERCISES_BY_ID["ex_py_pr3_threshold"]
    leaky = ex.solution.replace(
        "cf[num + ['plan', 'acquisition_source']], columns=['plan', 'acquisition_source']",
        "cf[num + ['plan', 'acquisition_source', 'cancellation_reason']].fillna({'cancellation_reason': 'none'}), columns=['plan', 'acquisition_source', 'cancellation_reason']",
    )
    g = grade_exercise(ex, leaky, RunSettings(timeout=60))
    assert not g.passed
    assert any("suspiciously high" in i.message for i in g.items if not i.passed)


def test_visualization_checks_inspect_figure():
    ex = EXERCISES_BY_ID["ex_py_vz4_fix"]
    g = grade_exercise(ex, ex.starter_code)
    failed = {i.name for i in g.items if not i.passed}
    assert "zero baseline" in failed and "honest title" in failed


def test_r_exercise_wrong_answer(rscript):
    if not rscript:
        pytest.skip("R not installed")
    ex = EXERCISES_BY_ID["ex_r_dg7_summary"]
    g = grade_exercise(ex, "churn_by_source <- data.frame(churned_6m = 1)\nhighest <- 'nope'", rscript=rscript)
    assert not g.passed and g.score == 0


def test_r_exercise_without_r_installed():
    g = grade_exercise(EXERCISES_BY_ID["ex_r_dg7_summary"], "x <- 1", rscript=None)
    assert not g.passed and "R is not installed" in g.summary
