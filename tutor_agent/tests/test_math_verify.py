import pytest

from tutor.domain import VerificationStatus as V
from tutor.tools import math_verify as mv
from tutor.tools.safe_parse import MathParseError, parse_math
from tutor.tools.units import check_quantity


@pytest.mark.parametrize("a,b", [("2x+2", "2(x+1)"), ("sin(x)^2+cos(x)^2", "1"), ("x^2-1", "(x-1)*(x+1)"),
                                 ("\\frac{1}{2}x", "x/2"), ("e^(ln(x))", "x")])
def test_equivalent_expressions(a, b):
    assert mv.check_expression(a, b).status == V.CORRECT


def test_non_equivalent_expression_reports_counterexample():
    r = mv.check_expression("x^2+1", "(x+1)^2")
    assert r.status == V.INCORRECT and "differ" in r.details


@pytest.mark.parametrize("bad", ["__import__('os')", "().__class__", "x.real", "lambda: 1", "'abc'", "open('f')"])
def test_unsafe_input_rejected(bad):
    with pytest.raises(MathParseError):
        parse_math(bad)


def test_parse_error_status_not_incorrect():
    assert mv.check_expression("x +* )", "x").status == V.PARSE_ERROR


def test_numeric_sign_and_factor_hints():
    assert mv.check_numeric("x = 4", "4").status == V.CORRECT
    assert "sign" in mv.check_numeric("-4", "4").details
    assert "factor of 100" in mv.check_numeric("250", "2.5").details
    assert mv.check_numeric("3/4", "0.75").status == V.CORRECT


def test_solution_sets():
    assert mv.check_solutions("x = 2 or x = -3", "-3, 2").status == V.CORRECT
    partial = mv.check_solutions("x = 2", "2, -3")
    assert partial.status == V.PARTIAL and partial.score == pytest.approx(0.5)
    assert mv.check_solutions("x = 5", "2, -3").status == V.INCORRECT


def test_verify_equation_solutions():
    assert mv.verify_equation_solutions("x^2 + x - 6 = 0", "2, -3").status == V.CORRECT
    assert mv.verify_equation_solutions("3x - 7 = 11", "4").status == V.INCORRECT


def test_step_checker_finds_earliest_error():
    checks = mv.check_steps("2x + 5 = 13\n2x = 18\nx = 9")
    first = mv.earliest_error(checks)
    assert first is not None and first.index == 1  # error appears in step 2, even though step 3 follows validly


def test_step_checker_expression_chain():
    checks = mv.check_steps("(x+1)^2 = x^2 + 2x + 1 = x^2 + 1")
    assert [c.ok for c in checks] == [True, True, False]


def test_correct_steps_have_no_error():
    assert mv.earliest_error(mv.check_steps("2x+5=13 => 2x=8 => x=4")) is None


def test_units():
    assert check_quantity("20 m/s", "72 km/h").status == V.CORRECT
    wrong_dim = check_quantity("20 m", "20 m/s")
    assert wrong_dim.status == V.INCORRECT and wrong_dim.data.get("dimension_mismatch")
    assert check_quantity("20", "20 m/s").data.get("units_missing")
    assert check_quantity("9.8 N", "9.8 kg*m/s^2").status == V.CORRECT
    assert check_quantity("3 x 10^8 m/s", "300000 km/s").status == V.CORRECT
