"""High-level runners for Python, SQL and R used by the UI and the graders."""

from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass, field

import pandas as pd

from analytics_lab.i18n import t
from analytics_lab.config import MAX_OUTPUT_CHARS, MAX_RESULT_ROWS, get_paths
from analytics_lab.data.loader import ensure_datasets
from analytics_lab.execution.sandbox import run_job


@dataclass
class RunSettings:
    timeout: int = 20
    backend: str = "local"
    docker_image: str = "analytics-lab-runner:latest"
    r_executable: str | None = None


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str = ""
    weight: float = 1.0


@dataclass
class PythonRun:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    error: str | None = None
    timed_out: bool = False
    figures: list[bytes] = field(default_factory=list)
    result: pd.DataFrame | None = None
    result_repr: str | None = None
    result_shape: tuple | None = None
    variables: list[dict] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    ref_error: str | None = None
    duration: float = 0.0


@dataclass
class SQLRun:
    ok: bool
    frame: pd.DataFrame | None = None
    types: list[str] = field(default_factory=list)
    error: str | None = None
    hint: str | None = None
    truncated: bool = False
    timed_out: bool = False
    duration: float = 0.0


# --------------------------------------------------------------------------- #
# Python                                                                       #
# --------------------------------------------------------------------------- #
def run_python(
    code: str,
    settings: RunSettings | None = None,
    preload: dict[str, str] | None = None,
    ref_code: str | None = None,
    checks: list[dict] | None = None,
    search_path: str | None = None,
) -> PythonRun:
    settings = settings or RunSettings()
    paths = get_paths()
    ensure_datasets(paths)
    if not code.strip():
        return PythonRun(ok=False, error=t("There is no code to run yet."))
    job = {
        "user_code": code,
        "ref_code": ref_code,
        "checks": checks or [],
        "preload": preload or {},
        "db_path": str(paths.warehouse_db),
        "search_path": search_path,
        "max_rows": 1000,
        "max_chars": MAX_OUTPUT_CHARS,
    }
    out = run_job("python_harness.py", job, settings.timeout, settings.backend, settings.docker_image)
    if out.payload is None:
        return PythonRun(ok=False, error=out.error, timed_out=out.timed_out, stdout=out.stdout[-MAX_OUTPUT_CHARS:], duration=out.duration)
    p = out.payload
    run = PythonRun(
        ok=bool(p["ok"]),
        stdout=p.get("stdout", ""),
        stderr=p.get("stderr", ""),
        error=p.get("error"),
        figures=[out.workdir_files[f] for f in p.get("figures", []) if f in out.workdir_files],
        variables=p.get("variables", []),
        checks=[CheckResult(c["name"], c["passed"], c.get("message", ""), c.get("weight", 1)) for c in p.get("checks", [])],
        ref_error=p.get("ref_error"),
        duration=float(p.get("duration", 0.0)),
    )
    if run.error:
        run.error = run.error + _python_hint(run.error)
    res = p.get("result")
    if res and res.get("kind") == "frame":
        try:
            run.result = pd.read_json(io.StringIO(res["data"]), orient="split")
            run.result_shape = tuple(res.get("shape", []))
        except ValueError:
            run.result_repr = "(result could not be displayed)"
    elif res:
        run.result_repr = res.get("repr")
    return run


_PY_HINTS = [
    (r"NameError: name '(\w+)' is not defined", "Is `{0}` spelled correctly and defined before it is used? Variables from earlier runs are not remembered; each run starts fresh."),
    (r"KeyError: '([^']+)'", "Column or key `{0}` does not exist. Print `df.columns` to see the available names (they are case-sensitive)."),
    (r"ModuleNotFoundError: No module named '([\w\.]+)'", "The package `{0}` is not installed in this environment. Use pandas, numpy, scipy, statsmodels, scikit-learn or matplotlib."),
    (r"IndentationError", "Python uses indentation to define blocks. Make sure lines inside a loop/function are indented consistently (4 spaces)."),
    (r"TypeError: unsupported operand", "You are combining values of incompatible types (e.g. text and numbers). Check dtypes with `df.dtypes`."),
    (r"ValueError: could not convert string to float", "A column contains text where numbers are expected. Use `pd.to_numeric(..., errors='coerce')` and decide how to handle invalid values."),
    (r"SettingWithCopyWarning", "Use `.loc[row_filter, 'column'] = value` or `.copy()` to avoid modifying a view."),
]


def _python_hint(error: str) -> str:
    for pat, hint in _PY_HINTS:
        m = re.search(pat, error)
        if m:
            return "\n\nHint: " + hint.format(*m.groups())
    return ""


# --------------------------------------------------------------------------- #
# SQL                                                                          #
# --------------------------------------------------------------------------- #
def run_sql_many(statements: dict[str, str], settings: RunSettings | None = None, search_path: str | None = None, max_rows: int = 50_000) -> dict[str, SQLRun]:
    """Execute several queries in one child process (e.g. learner + reference)."""
    settings = settings or RunSettings()
    paths = get_paths()
    ensure_datasets(paths)
    job = {
        "db_path": str(paths.warehouse_db),
        "uploads_path": str(paths.uploads_db) if paths.uploads_db.exists() else None,
        "search_path": search_path,
        "statements": [{"id": k, "sql": v} for k, v in statements.items()],
        "max_rows": max_rows,
    }
    out = run_job("sql_harness.py", job, settings.timeout, settings.backend, settings.docker_image)
    if out.payload is None:
        err = SQLRun(ok=False, error=out.error, timed_out=out.timed_out, duration=out.duration)
        return {k: err for k in statements}
    if out.payload.get("setup_error"):
        err = SQLRun(ok=False, error="Could not open the database: " + out.payload["setup_error"])
        return {k: err for k in statements}
    results = {}
    for k, r in out.payload["results"].items():
        if not r["ok"]:
            results[k] = SQLRun(ok=False, error=r["error"], hint=sql_hint(r["error"]), duration=r["duration"])
            continue
        frame = pd.DataFrame(r["rows"], columns=_dedupe(r["columns"])) if r["columns"] else pd.DataFrame()
        results[k] = SQLRun(ok=True, frame=frame, types=r["types"], truncated=r["truncated"], duration=r["duration"])
    return results


def run_sql(query: str, settings: RunSettings | None = None, search_path: str | None = None, max_rows: int = MAX_RESULT_ROWS) -> SQLRun:
    if not query.strip():
        return SQLRun(ok=False, error=t("There is no query to run yet."))
    return run_sql_many({"q": query}, settings, search_path, max_rows)["q"]


def _dedupe(cols: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            out.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            out.append(c)
    return out


_SQL_HINTS = [
    (r"must appear in the GROUP BY clause|must be part of an aggregate", "Every selected column must either be in GROUP BY or wrapped in an aggregate such as SUM() or COUNT()."),
    (r'Referenced column "?(\w+)"? not found', "Column `{0}` does not exist in the tables you referenced. Check spelling, table aliases and the schema panel."),
    (r"Table with name (\w+) does not exist", "Table `{0}` was not found. Qualify it with its schema (e.g. `retail.orders`) or check the table list."),
    (r"Parser Error: syntax error at or near \"?(\w+)\"?", "Syntax error near `{0}`. Check commas between columns, a missing FROM, or a keyword used as a column name."),
    (r"Ambiguous reference to column name \"?(\w+)\"?", "`{0}` exists in more than one joined table. Prefix it with a table alias, e.g. `o.{0}`."),
    (r"WHERE clause cannot contain aggregates", "Filter aggregated values with HAVING (after GROUP BY), not WHERE."),
    (r"Could not convert string|Conversion Error", "A value could not be converted to the requested type. Compare like with like, e.g. DATE '2024-01-01' instead of a plain string, or use TRY_CAST."),
    (r"read-only|read only", "The lab databases are read-only: write queries (INSERT, UPDATE, CREATE TABLE) are not allowed. Use a CTE or subquery instead."),
    (r"external access|Permission Error", "Reading files or URLs from SQL is disabled in the lab for safety. Query the provided tables or import files via the Upload tab."),
]


def sql_hint(error: str | None) -> str | None:
    if not error:
        return None
    for pat, hint in _SQL_HINTS:
        m = re.search(pat, error, re.IGNORECASE)
        if m:
            return t(hint).format(*m.groups())
    return None


# --------------------------------------------------------------------------- #
# R (optional)                                                                 #
# --------------------------------------------------------------------------- #
@dataclass
class RRun:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    error: str | None = None
    timed_out: bool = False
    figures: list[bytes] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    duration: float = 0.0


R_DRIVER = r"""
args <- commandArgs(trailingOnly = TRUE)
.lab_csv_dir <- readLines("csv_dir.txt", warn = FALSE)[1]
load_table <- function(name) {
  parts <- strsplit(name, ".", fixed = TRUE)[[1]]
  utils::read.csv(file.path(.lab_csv_dir, parts[1], paste0(parts[2], ".csv")), stringsAsFactors = FALSE)
}
.lab_preload <- if (file.exists("preload.tsv")) utils::read.delim("preload.tsv", header = FALSE, stringsAsFactors = FALSE) else NULL
.lab_env <- function() {
  e <- new.env(parent = globalenv())
  if (!is.null(.lab_preload)) for (i in seq_len(nrow(.lab_preload))) assign(.lab_preload[i, 1], load_table(.lab_preload[i, 2]), envir = e)
  e
}
.lab_res <- file("results.tsv", open = "w", encoding = "UTF-8")
.lab_clean <- function(x) gsub("[\t\r\n]+", " ", x)
ref <- .lab_env()
if (file.exists("ref.R")) {
  tryCatch(invisible(capture.output(eval(parse(file = "ref.R"), envir = ref))),
           error = function(e) writeLines(paste0("REF_ERROR\t", .lab_clean(conditionMessage(e))), .lab_res))
}
user <- .lab_env()
grDevices::png(file.path(getwd(), "figure_%d.png"), width = 800, height = 550)
.lab_user_ok <- tryCatch({ eval(parse(file = "user.R"), envir = user); TRUE },
  error = function(e) { writeLines(paste0("USER_ERROR\t", .lab_clean(conditionMessage(e))), .lab_res); message("Error: ", conditionMessage(e)); FALSE })
invisible(grDevices::dev.off())
.lab_checks <- sort(list.files(pattern = "^check_[0-9]+\\.R$"))
for (f in .lab_checks) {
  id <- sub("^check_([0-9]+)\\.R$", "\\1", f)
  if (!.lab_user_ok) { writeLines(paste0("CHECK\t", id, "\tFAIL\tNot evaluated because your code raised an error."), .lab_res); next }
  ok <- tryCatch(isTRUE(eval(parse(file = f), envir = new.env(parent = globalenv()))),
                 error = function(e) { writeLines(paste0("CHECK\t", id, "\tFAIL\t", .lab_clean(conditionMessage(e))), .lab_res); NA })
  if (!is.na(ok)) writeLines(paste0("CHECK\t", id, "\t", if (ok) "PASS" else "FAIL", "\t"), .lab_res)
}
close(.lab_res)
cat("\n", args[1], "\n", sep = "")
"""


def run_r(
    code: str,
    rscript: str,
    settings: RunSettings | None = None,
    preload: dict[str, str] | None = None,
    ref_code: str | None = None,
    checks: list[dict] | None = None,
) -> RRun:
    """Run R code through ``Rscript``. Checks are R expressions evaluated with
    ``user`` and ``ref`` environments in scope that must return TRUE."""
    settings = settings or RunSettings()
    paths = get_paths()
    ensure_datasets(paths)
    if not code.strip():
        return RRun(ok=False, error=t("There is no code to run yet."))
    files = {"driver.R": R_DRIVER, "user.R": code, "csv_dir.txt": str(paths.csv_dir).replace("\\", "/")}
    if ref_code:
        files["ref.R"] = ref_code
    if preload:
        files["preload.tsv"] = "\n".join(f"{k}\t{v}" for k, v in preload.items()) + "\n"
    checks = checks or []
    for i, chk in enumerate(checks):
        files[f"check_{i:02d}.R"] = chk["code"]
    out = _run_r_process(rscript, files, settings.timeout)
    if out.timed_out:
        return RRun(ok=False, timed_out=True, error=out.error, duration=out.duration)
    if out.error and "results.tsv" not in out.workdir_files:
        return RRun(ok=False, error=out.error, stdout=out.stdout, stderr=out.stderr)
    lines = out.workdir_files.get("results.tsv", b"").decode("utf-8", "replace").splitlines()
    user_err = next((ln.split("\t", 1)[1] for ln in lines if ln.startswith("USER_ERROR")), None)
    status = {}
    for ln in lines:
        if ln.startswith("CHECK\t"):
            parts = (ln.split("\t") + ["", "", "", ""])[:4]
            status[int(parts[1])] = (parts[2] == "PASS", parts[3])
    results = []
    for i, chk in enumerate(checks):
        passed, msg = status.get(i, (False, "Check did not run."))
        results.append(CheckResult(chk["name"], passed, msg or ("" if passed else chk.get("hint", "Check failed.")), chk.get("weight", 1)))
    figs = [v for k, v in sorted(out.workdir_files.items()) if k.endswith(".png") and len(v) > 2000]
    stdout = out.stdout.split("\n@@R-DONE")[0] if out.stdout else ""
    return RRun(ok=user_err is None, stdout=stdout[-MAX_OUTPUT_CHARS:], stderr=out.stderr[-MAX_OUTPUT_CHARS:], error=user_err,
                figures=figs, checks=results, duration=out.duration)


def _run_r_process(rscript: str, files: dict[str, str], timeout: int):
    """R does not use the JSON/nonce protocol; run it directly in a temp dir."""
    import shutil
    import subprocess
    import tempfile
    import time
    from pathlib import Path

    from analytics_lab.execution.sandbox import ProcessOutcome, safe_env

    workdir = Path(tempfile.mkdtemp(prefix="lab_r_"))
    try:
        for name, content in files.items():
            (workdir / name).write_text(content, encoding="utf-8")
        env = safe_env(workdir)
        start = time.perf_counter()
        try:
            proc = subprocess.run([rscript, "--vanilla", "driver.R", "@@R-DONE"], cwd=str(workdir), env=env, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired:
            return ProcessOutcome(None, timed_out=True, duration=time.perf_counter() - start, error=t("R execution stopped after {n} seconds.", n=timeout))
        except OSError as exc:
            return ProcessOutcome(None, error=f"Could not start Rscript ({rscript}): {exc}")
        collected = {p.name: p.read_bytes() for p in workdir.iterdir() if p.suffix in (".png", ".tsv")}
        err = None if proc.returncode == 0 else f"Rscript exited with code {proc.returncode}.\n{proc.stderr[-1500:]}"
        return ProcessOutcome(None, proc.stdout, proc.stderr, False, proc.returncode, time.perf_counter() - start, collected, err)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def to_json_records(df: pd.DataFrame) -> str:
    return json.dumps(json.loads(df.to_json(orient="records", date_format="iso")), indent=2)
