"""Isolated execution of student / exercise Python code.

Layers of protection:
1. Static AST validation: whitelisted imports only, no eval/exec/open/
   __import__, no dangerous dunder attribute access.
2. A separate interpreter started with ``-I -S -B`` (isolated mode: no user
   site-packages, no environment variables), a throw-away working directory and
   a minimal environment.
3. An in-process audit hook in the child that blocks file writes, reads outside
   the Python installation, sockets, subprocesses, ctypes, registry access etc.
4. Wall-clock timeout, output size cap, and on Windows a Job Object limiting
   memory and forbidding child processes.

This is a defence-in-depth sandbox for small educational exercises; it is not
a guarantee against a determined attacker (see README "Known limitations").
"""

from __future__ import annotations

import ast
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from tutor.domain import CodeTest, VerificationResult, VerificationStatus

log = logging.getLogger(__name__)

ALLOWED_IMPORTS = {
    "math", "cmath", "itertools", "functools", "collections", "heapq", "bisect", "string", "re",
    "statistics", "random", "typing", "dataclasses", "fractions", "decimal", "operator", "copy",
    "enum", "abc", "array", "datetime", "textwrap", "numbers",
}
BANNED_NAMES = {
    "eval", "exec", "compile", "open", "__import__", "input", "breakpoint", "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "memoryview", "help", "exit", "quit", "__builtins__", "__loader__",
    "__spec__", "classmethod.__func__",
}
BANNED_ATTRS = {
    "__class__", "__bases__", "__base__", "__subclasses__", "__globals__", "__builtins__", "__dict__",
    "__code__", "__mro__", "__getattribute__", "__loader__", "__spec__", "__closure__", "__func__",
    "__self__", "__module__", "__reduce__", "__reduce_ex__", "__import__", "f_globals", "f_locals",
    "f_back", "gi_frame", "cr_frame", "tb_frame", "__traceback__",
}
MAX_CODE_CHARS = 20_000
MAX_OUTPUT_CHARS = 8_000


class CodeRejected(ValueError):
    pass


def validate_code(code: str) -> None:
    if len(code) > MAX_CODE_CHARS:
        raise CodeRejected("Code is too long for the exercise sandbox.")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise CodeRejected(f"SyntaxError on line {exc.lineno}: {exc.msg}") from exc
    _check_tree(tree)


def _check_tree(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    raise CodeRejected(f"Import of '{alias.name}' is not allowed in the exercise sandbox.")
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                raise CodeRejected(f"Import from '{node.module}' is not allowed in the exercise sandbox.")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            raise CodeRejected(f"Use of '{node.id}' is not allowed in the exercise sandbox.")
        elif isinstance(node, ast.Attribute) and (node.attr in BANNED_ATTRS or node.attr.startswith("f_")):
            raise CodeRejected(f"Access to attribute '{node.attr}' is not allowed.")
        elif isinstance(node, (ast.Global, ast.Nonlocal)) and any(n.startswith("__") for n in node.names):
            raise CodeRejected("Not allowed.")


def validate_test_call(call: str) -> None:
    try:
        tree = ast.parse(call, mode="eval")
    except SyntaxError as exc:
        raise CodeRejected(f"Invalid test expression: {call!r}") from exc
    _check_tree(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Lambda, ast.NamedExpr, ast.Await, ast.Yield, ast.YieldFrom)):
            raise CodeRejected(f"Unsupported construct in test: {call!r}")


# The child-side harness. It is written to the sandbox directory and executed with -I.
_HARNESS = r'''
import sys, json, io, os, ast, math, contextlib, traceback
_payload = json.loads(sys.stdin.read())
_ALLOWED = tuple(os.path.normcase(os.path.abspath(p)) for p in (sys.prefix, sys.base_prefix, sys.exec_prefix, os.getcwd()))
_BLOCK = ("socket.", "subprocess.", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.startfile",
          "os.kill", "os.remove", "os.unlink", "os.rmdir", "os.rename", "os.replace", "os.mkdir", "os.chmod",
          "os.putenv", "os.unsetenv", "os.truncate", "os.link", "os.symlink", "shutil.", "ctypes.", "winreg.",
          "_winapi.", "msvcrt.", "webbrowser.", "urllib.", "http.", "ftplib.", "smtplib.", "sqlite3.",
          "os.chdir", "os.fork", "glob.", "pty.", "signal.")
def _inside(path):
    p = os.path.normcase(os.path.abspath(os.fsdecode(path)))
    return p.startswith(_ALLOWED)
def _hook(event, args):
    if event in ("os.listdir", "os.scandir"):
        if args and args[0] is not None and not isinstance(args[0], int) and not _inside(args[0]):
            raise PermissionError("Directory listing is disabled in the sandbox")
    elif event == "open":
        path, mode = args[0], args[1] if len(args) > 1 else "r"
        if mode and any(c in str(mode) for c in "wax+"):
            raise PermissionError("Writing files is disabled in the sandbox")
        if isinstance(path, int):
            return
        if not _inside(path):
            raise PermissionError("Reading files is disabled in the sandbox")
    elif event.startswith(_BLOCK) or (event == "import" and str(args[0]).split(".")[0] in ("ctypes", "socket", "subprocess", "_socket", "winreg", "_winapi", "multiprocessing", "_ctypes")):
        raise PermissionError("Blocked in sandbox: " + event)
sys.addaudithook(_hook)
_real_stdout = sys.stdout
_buf = io.StringIO()
_result = {"ok": True, "error": None, "stdout": "", "tests": []}
_ns = {"__name__": "__main__"}
try:
    with contextlib.redirect_stdout(_buf), contextlib.redirect_stderr(_buf):
        exec(compile(_payload["code"], "<student>", "exec"), _ns)
except BaseException as e:
    _result["ok"] = False
    tb = traceback.extract_tb(e.__traceback__)
    line = next((f.lineno for f in reversed(tb) if f.filename == "<student>"), None)
    _result["error"] = {"type": type(e).__name__, "message": str(e)[:500], "line": line}
for t in _payload.get("tests", []):
    entry = {"call": t["call"], "expected": t["expected"], "passed": False, "got": None, "error": None}
    if _result["error"] is None:
        try:
            with contextlib.redirect_stdout(_buf):
                got = eval(compile(t["call"], "<test>", "eval"), _ns)
            exp = ast.literal_eval(t["expected"])
            if isinstance(exp, float) or isinstance(got, float):
                passed = isinstance(got, (int, float)) and math.isclose(got, exp, rel_tol=1e-9, abs_tol=1e-9)
            else:
                passed = got == exp
            entry.update(passed=bool(passed), got=repr(got)[:300])
        except BaseException as e:
            entry["error"] = type(e).__name__ + ": " + str(e)[:300]
    _result["tests"].append(entry)
_result["stdout"] = _buf.getvalue()[:%(max_out)d]
_real_stdout.write("\n@@RESULT@@" + json.dumps(_result))
_real_stdout.flush()
''' % {"max_out": MAX_OUTPUT_CHARS}


@dataclass
class RunResult:
    ok: bool
    stdout: str = ""
    error: dict | None = None
    tests: list[dict] = field(default_factory=list)
    timed_out: bool = False
    rejected: str = ""

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.get("passed"))

    def summary(self) -> str:
        if self.rejected:
            return f"Not executed: {self.rejected}"
        if self.timed_out:
            return "Execution stopped: time limit exceeded (possible infinite loop)."
        parts = []
        if self.error:
            loc = f" on line {self.error.get('line')}" if self.error.get("line") else ""
            parts.append(f"{self.error['type']}{loc}: {self.error['message']}")
        if self.tests:
            parts.append(f"{self.passed}/{len(self.tests)} tests passed")
        return "; ".join(parts) or "Ran successfully."


class _WindowsJob:
    """Best-effort Job Object: memory cap, no child processes, kill on close."""

    def __init__(self, memory_mb: int):
        self.handle = None
        if os.name != "nt":
            return
        try:
            import ctypes
            from ctypes import wintypes

            k32 = ctypes.WinDLL("kernel32", use_last_error=True)

            class IO_COUNTERS(ctypes.Structure):
                _fields_ = [(n, ctypes.c_ulonglong) for n in (
                    "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                    "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

            class BASIC(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

            class EXTENDED(ctypes.Structure):
                _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS),
                            ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                            ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

            k32.CreateJobObjectW.restype = wintypes.HANDLE
            job = k32.CreateJobObjectW(None, None)
            if not job:
                return
            info = EXTENDED()
            info.BasicLimitInformation.LimitFlags = 0x100 | 0x2000 | 0x8  # PROCESS_MEMORY | KILL_ON_JOB_CLOSE | ACTIVE_PROCESS
            info.BasicLimitInformation.ActiveProcessLimit = 1
            info.ProcessMemoryLimit = memory_mb * 1024 * 1024
            if not k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
                k32.CloseHandle(job)
                return
            self.handle, self._k32 = job, k32
        except Exception as exc:  # pragma: no cover - platform specific
            log.info("Job object unavailable: %s", exc)

    def assign(self, proc: subprocess.Popen) -> bool:
        if not self.handle:
            return False
        try:
            return bool(self._k32.AssignProcessToJobObject(self.handle, int(proc._handle)))  # type: ignore[attr-defined]
        except Exception:
            return False

    def close(self) -> None:
        if self.handle:
            self._k32.CloseHandle(self.handle)
            self.handle = None


class CodeRunner:
    def __init__(self, sandbox_root: Path, timeout_s: float = 5.0, memory_mb: int = 256, python: str | None = None):
        self.sandbox_root = Path(sandbox_root)
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        self.timeout_s = timeout_s
        self.memory_mb = memory_mb
        # A venv python.exe is a launcher that spawns the real interpreter, which the Job
        # Object (no child processes) would block, so use the base interpreter directly.
        self.python = python or getattr(sys, "_base_executable", None) or sys.executable

    def run(self, code: str, tests: list[CodeTest] | None = None) -> RunResult:
        tests = tests or []
        try:
            validate_code(code)
            for t in tests:
                validate_test_call(t.call)
        except CodeRejected as exc:
            return RunResult(ok=False, rejected=str(exc))

        workdir = Path(tempfile.mkdtemp(prefix="run_", dir=self.sandbox_root))
        harness = workdir / "harness.py"
        harness.write_text(_HARNESS, encoding="utf-8")
        payload = json.dumps({"code": code, "tests": [t.model_dump() for t in tests]})
        env = {"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"), "PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": "0"}
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        job = _WindowsJob(self.memory_mb)
        try:
            proc = subprocess.Popen(
                [self.python, "-I", "-S", "-B", str(harness)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=workdir, env=env, creationflags=flags,
            )
            job.assign(proc)
            try:
                out, err = proc.communicate(payload.encode("utf-8"), timeout=self.timeout_s)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                return RunResult(ok=False, timed_out=True)
            text = out.decode("utf-8", "replace")
            if "@@RESULT@@" not in text:
                msg = err.decode("utf-8", "replace")[-500:] or "The process ended unexpectedly (memory limit?)."
                return RunResult(ok=False, error={"type": "SandboxError", "message": msg, "line": None})
            data = json.loads(text.rsplit("@@RESULT@@", 1)[1])
            return RunResult(ok=data["ok"], stdout=data["stdout"], error=data["error"], tests=data["tests"])
        finally:
            job.close()
            shutil.rmtree(workdir, ignore_errors=True)

    def verify(self, code: str, tests: list[CodeTest]) -> tuple[VerificationResult, RunResult]:
        res = self.run(code, tests)
        method = "Isolated Python execution with predefined test cases"
        if res.rejected:
            status = VerificationStatus.PARSE_ERROR
        elif res.timed_out or (res.error and not res.tests):
            status = VerificationStatus.INCORRECT
        elif tests:
            ratio = res.passed / len(tests)
            status = VerificationStatus.CORRECT if ratio == 1 else (VerificationStatus.PARTIAL if ratio > 0 else VerificationStatus.INCORRECT)
        else:
            status = VerificationStatus.UNVERIFIABLE if res.ok else VerificationStatus.INCORRECT
        lines = [res.summary()]
        for t in res.tests[:10]:
            mark = "✔" if t["passed"] else "✘"
            got = t["error"] or t["got"]
            lines.append(f"{mark} `{t['call']}` → expected `{t['expected']}`, got `{got}`")
        return VerificationResult(
            status=status, method=method, details="\n".join(lines),
            score=(res.passed / len(tests)) if tests else None,
            data={"stdout": res.stdout[:2000], "error": res.error},
        ), res
