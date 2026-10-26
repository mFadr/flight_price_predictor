import pytest

from tutor.domain import CodeTest, VerificationStatus
from tutor.tools import code_runner as cr


@pytest.fixture
def runner(tmp_path):
    return cr.CodeRunner(tmp_path / "sandbox", timeout_s=4, memory_mb=200)


def test_tests_pass_and_fail(runner):
    res = runner.run("def add(a, b):\n    return a + b\nprint('hello')",
                     [CodeTest(call="add(2, 3)", expected="5"), CodeTest(call="add(1, 1)", expected="3")])
    assert res.ok and res.stdout.strip() == "hello"
    assert [t["passed"] for t in res.tests] == [True, False]


def test_verify_partial_credit(runner):
    vr, _ = runner.verify("def sq(x):\n    return x * 2", [CodeTest(call="sq(2)", expected="4"), CodeTest(call="sq(3)", expected="9")])
    assert vr.status == VerificationStatus.PARTIAL and vr.score == 0.5


@pytest.mark.parametrize("code", [
    "import os\nos.system('echo hi')",
    "import subprocess",
    "import socket",
    "open('x.txt', 'w')",
    "eval('1+1')",
    "__import__('os')",
    "x = ().__class__.__bases__[0].__subclasses__()",
    "from pathlib import Path",
])
def test_static_rejection(runner, code):
    res = runner.run(code)
    assert res.rejected


def test_runtime_audit_hook_blocks_file_write(runner, monkeypatch):
    # Bypass the static check to prove the second (runtime) layer also blocks writes.
    monkeypatch.setattr(cr, "validate_code", lambda code: None)
    res = runner.run("f = open('evil.txt', 'w')\nf.write('x')")
    assert not res.ok and res.error["type"] == "PermissionError"


def test_runtime_audit_hook_blocks_reading_user_files(runner, monkeypatch, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret")
    monkeypatch.setattr(cr, "validate_code", lambda code: None)
    res = runner.run(f"print(open(r'{secret}').read())")
    assert not res.ok and "top secret" not in res.stdout


def test_timeout(runner):
    res = runner.run("while True:\n    pass")
    assert res.timed_out


def test_error_line_reported(runner):
    res = runner.run("x = 1\ny = x / 0")
    assert res.error["type"] == "ZeroDivisionError" and res.error["line"] == 2


def test_float_tolerance(runner):
    res = runner.run("def f():\n    return 0.1 + 0.2", [CodeTest(call="f()", expected="0.3")])
    assert res.tests[0]["passed"]


def test_whitelisted_imports_work(runner):
    res = runner.run("import math, statistics\nprint(statistics.mean([1, 2, 3]), math.sqrt(16))")
    assert res.ok and "2 4.0" in res.stdout
