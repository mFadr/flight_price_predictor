"""Code execution: isolation, timeouts, error reporting, SQL read-only enforcement, R."""

import os

import pytest

from analytics_lab.execution.runners import RunSettings, run_python, run_r, run_sql, run_sql_many, sql_hint
from analytics_lab.execution.sandbox import docker_command


def test_python_runs_with_preload_result_and_figure():
    r = run_python(
        "print('hello')\nresult = orders.groupby('region').size().rename('n').to_frame()\nfig, ax = plt.subplots(); ax.plot([1, 2])",
        preload={"orders": "retail.orders"},
    )
    assert r.ok, r.error
    assert "hello" in r.stdout
    assert r.result is not None and len(r.result) == 5
    assert len(r.figures) == 1 and r.figures[0][:4] == b"\x89PNG"


def test_python_error_is_readable_with_hint():
    r = run_python("x = 1\ny = undefined_name + x")
    assert not r.ok
    assert "NameError" in r.error and "line 2" in r.error and "Hint" in r.error


def test_python_syntax_error():
    r = run_python("for i in range(3)\n    print(i)")
    assert not r.ok and "SyntaxError" in r.error


def test_python_timeout():
    r = run_python("while True:\n    pass", RunSettings(timeout=3))
    assert r.timed_out and not r.ok and "3 seconds" in r.error


def test_child_does_not_inherit_secrets(monkeypatch):
    monkeypatch.setenv("SUPER_SECRET_API_KEY", "abc123")
    r = run_python("import os\nprint(os.environ.get('SUPER_SECRET_API_KEY'))")
    assert r.ok and "abc123" not in r.stdout


def test_child_runs_in_temporary_directory():
    r = run_python("import os\nprint(os.getcwd())")
    assert r.ok
    assert "lab_run_" in r.stdout
    assert not os.path.exists(r.stdout.strip())  # cleaned up afterwards


def test_sql_query_and_types():
    r = run_sql("SELECT region, COUNT(*) AS n FROM orders GROUP BY 1 ORDER BY 2 DESC", search_path="retail")
    assert r.ok and len(r.frame) == 5 and r.types == ["VARCHAR", "BIGINT"]


def test_sql_is_read_only():
    r = run_sql("CREATE TABLE retail.hack AS SELECT 1")
    assert not r.ok and "read-only" in r.error.lower()
    assert "read-only" in (r.hint or "")


def test_sql_external_access_disabled(tmp_path):
    f = tmp_path / "secret.csv"
    f.write_text("a\n1\n")
    r = run_sql(f"SELECT * FROM read_csv('{f.as_posix()}')")
    assert not r.ok


def test_sql_error_hints():
    r = run_sql("SELECT regin FROM retail.orders")
    assert not r.ok and "regin" in (r.hint or "")
    assert "HAVING" in sql_hint("Binder Error: WHERE clause cannot contain aggregates!")


def test_sql_many_isolated_failures():
    res = run_sql_many({"good": "SELECT 1 AS x", "bad": "SELEC 1"})
    assert res["good"].ok and not res["bad"].ok


def test_empty_code_is_rejected():
    assert not run_python("   ").ok
    assert not run_sql("").ok


def test_docker_command_is_locked_down(tmp_path):
    cmd = docker_command("img", tmp_path, tmp_path, "python_harness.py", ["python", "-I"])
    joined = " ".join(cmd)
    assert "--network none" in joined and "--read-only" in joined and ":ro" in joined and "--memory" in joined


def test_r_runs_when_available(rscript):
    if not rscript:
        pytest.skip("R not installed")
    r = run_r("x <- mean(cf$logins_first_month)\nprint(round(x, 1))\nhist(cf$logins_first_month)", rscript, preload={"cf": "subscription.churn_features"})
    assert r.ok, r.error
    assert len(r.figures) == 1


def test_r_error_reported(rscript):
    if not rscript:
        pytest.skip("R not installed")
    r = run_r("stop('custom failure')", rscript)
    assert not r.ok and "custom failure" in r.error
