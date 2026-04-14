"""Automated assessment: multiple choice, SQL result-set comparison, Python/R checks.

SQL answers are compared on the *returned data* (column mapping, row counts,
values with numeric tolerance, ordering when required) - never on query text -
so any equivalent query earns full credit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from analytics_lab.execution.runners import PythonRun, RRun, RunSettings, SQLRun, run_python, run_r, run_sql_many
from analytics_lab.i18n import t
from analytics_lab.models import Exercise, Question


# --------------------------------------------------------------------------- #
# Multiple choice                                                              #
# --------------------------------------------------------------------------- #
@dataclass
class MCQResult:
    correct: bool
    chosen: list[int]
    correct_keys: list[int]
    partial: float  # 0..1 (multi-select partial credit is reported but 'correct' needs an exact match)


def grade_mcq(question: Question, chosen: list[int]) -> MCQResult:
    chosen_set = set(chosen)
    keys = question.correct_keys
    correct = chosen_set == keys
    if question.qtype == "multi":
        hits = len(chosen_set & keys)
        wrong = len(chosen_set - keys)
        partial = max(0.0, (hits - wrong) / len(keys))
    else:
        partial = 1.0 if correct else 0.0
    return MCQResult(correct, sorted(chosen_set), sorted(keys), partial)


# --------------------------------------------------------------------------- #
# Coding exercises                                                             #
# --------------------------------------------------------------------------- #
@dataclass
class CheckItem:
    name: str
    passed: bool
    message: str = ""
    weight: float = 1.0


@dataclass
class GradeResult:
    passed: bool
    score: float
    items: list[CheckItem] = field(default_factory=list)
    summary: str = ""
    next_step: str = ""
    error: str | None = None
    hint: str | None = None
    user_frame: pd.DataFrame | None = None
    expected_preview: pd.DataFrame | None = None  # only shown after the attempt, never before
    run: PythonRun | RRun | SQLRun | None = None
    content_error: str | None = None


def grade_exercise(ex: Exercise, code: str, settings: RunSettings | None = None, rscript: str | None = None) -> GradeResult:
    settings = settings or RunSettings()
    if not code.strip():
        return GradeResult(False, 0.0, summary=t("Nothing to grade yet - write some code first."), next_step=t("Start from the starter code and the first requirement."))
    if ex.language == "sql":
        return grade_sql(ex, code, settings)
    if ex.language == "python":
        return grade_python(ex, code, settings)
    if ex.language == "r":
        if not rscript:
            return GradeResult(False, 0.0, summary=t("R is not installed, so this exercise cannot be executed."), next_step=t("Install R (see Settings & Help) or choose a Python/SQL exercise."))
        return grade_r(ex, code, settings, rscript)
    raise ValueError(f"Unsupported language {ex.language}")


# ---------------------------------------------------------------- SQL ------
def _norm_cell(v):
    if isinstance(v, str):
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[T ]00:00:00(\.0+)?", v)
        if m:
            return m.group(1)
        return v.strip()
    return v


def _norm_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    for c in out.columns:
        out[c] = out[c].map(_norm_cell)
    return out


def _col_equal(a: pd.Series, b: pd.Series, tol: float) -> tuple[bool, int | None]:
    """Compare two aligned columns; returns (equal, first_bad_index)."""
    an = pd.to_numeric(a, errors="coerce")
    bn = pd.to_numeric(b, errors="coerce")
    both_numeric = bn.notna().sum() == b.notna().sum() and an.notna().sum() == a.notna().sum() and b.notna().any()
    if both_numeric:
        av, bv = an.to_numpy(float), bn.to_numpy(float)
        ok = np.isclose(av, bv, rtol=1e-6, atol=tol, equal_nan=True)
    else:
        av = a.astype(object).where(a.notna(), None).map(lambda x: str(x).lower() if isinstance(x, bool) else x).astype(str).to_numpy()
        bv = b.astype(object).where(b.notna(), None).map(lambda x: str(x).lower() if isinstance(x, bool) else x).astype(str).to_numpy()
        ok = av == bv
    if ok.all():
        return True, None
    return False, int(np.argmin(ok))


def _sort_key_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Sort rows deterministically, rounding numbers so tiny float noise does not change order."""
    tmp = df.copy()
    keys = []
    for c in tmp.columns:
        num = pd.to_numeric(tmp[c], errors="coerce")
        k = f"__k_{c}"
        tmp[k] = num.round(4).astype(str) if num.notna().sum() == tmp[c].notna().sum() and tmp[c].notna().any() else tmp[c].astype(str)
        keys.append(k)
    return df.loc[tmp.sort_values(keys, kind="mergesort").index].reset_index(drop=True)


def compare_result_sets(user: pd.DataFrame, expected: pd.DataFrame, order_matters: bool = False, tol: float = 0.01) -> tuple[list[CheckItem], float]:
    """Compare a learner's SQL result with the expected result. Returns check items and a 0-100 score."""
    items: list[CheckItem] = []
    u, e = _norm_frame(user), _norm_frame(expected)
    score = 0.0

    # Columns ---------------------------------------------------------------
    exp_cols = list(e.columns)
    missing = [c for c in exp_cols if c not in u.columns]
    extra = [c for c in u.columns if c not in exp_cols]
    if not missing:
        mapping = {c: c for c in exp_cols}
        if extra:
            items.append(CheckItem("Columns", False, t("All expected columns are present, but you also returned {extra}. Return only: {cols}.", extra=extra, cols=exp_cols), 20))
            score += 10
        else:
            items.append(CheckItem("Columns", True, t("Column names match."), 20))
            score += 20
    elif len(u.columns) == len(exp_cols):
        mapping = dict(zip(exp_cols, u.columns))
        items.append(CheckItem("Columns", False, t("Column names differ - expected {cols}, got {got}. Values are compared by position; rename with AS.", cols=exp_cols, got=list(u.columns)), 20))
        score += 5
    else:
        items.append(CheckItem("Columns", False, t("Expected {n} columns {cols}; your result has {m}: {got}. Missing: {missing}.", n=len(exp_cols), cols=exp_cols, m=len(u.columns), got=list(u.columns), missing=missing), 20))
        mapping = {c: c for c in exp_cols if c in u.columns}

    # Rows ------------------------------------------------------------------
    if len(u) == len(e):
        items.append(CheckItem("Row count", True, t("{n} rows, as expected.", n=len(e)), 20))
        score += 20
    else:
        direction = t("more") if len(u) > len(e) else t("fewer")
        why = (t("Too many rows often means a missing filter, a missing GROUP BY level being collapsed, or a join that duplicates rows.")
               if len(u) > len(e) else t("Too few rows often means an over-restrictive filter, an INNER JOIN that drops unmatched rows, or a LIMIT."))
        items.append(CheckItem("Row count", False, t("Expected {n} rows; your result has {m} ({direction}).", n=len(e), m=len(u), direction=direction) + f" {why}", 20))

    # Values ----------------------------------------------------------------
    if len(u) == len(e) and mapping and len(mapping) == len(exp_cols):
        uu = pd.DataFrame({c: u[mapping[c]].values for c in exp_cols})
        ee = e[exp_cols].reset_index(drop=True)
        in_order_ok = all(_col_equal(uu[c], ee[c], tol)[0] for c in exp_cols)
        if in_order_ok:
            items.append(CheckItem("Values", True, t("All values match."), 60))
            score += 60
            if order_matters:
                items.append(CheckItem("Ordering", True, t("Rows are in the required order."), 0))
        else:
            us, es = _sort_key_frame(uu), _sort_key_frame(ee)
            sorted_ok = True
            first_bad = None
            for c in exp_cols:
                ok, idx = _col_equal(us[c], es[c], tol)
                if not ok:
                    sorted_ok = False
                    first_bad = (c, idx, es[c].iloc[idx], us[c].iloc[idx])
                    break
            if sorted_ok and order_matters:
                items.append(CheckItem("Values", True, t("All values match."), 60))
                items.append(CheckItem("Ordering", False, t("The rows are correct but not in the required order. Check your ORDER BY (direction and tie-breakers)."), 0))
                score += 40
            elif sorted_ok:
                items.append(CheckItem("Values", True, t("All values match (row order is not assessed for this exercise)."), 60))
                score += 60
            else:
                c, idx, exp_v, got_v = first_bad
                n_bad_cols = sum(not _col_equal(us[k], es[k], tol)[0] for k in exp_cols)
                items.append(CheckItem("Values", False,
                                       t("Values differ in {n} column(s). First difference in column '{c}': expected {exp}, got {got}. "
                                         "Check filters (status, dates), NULL handling and rounding.", n=n_bad_cols, c=c, exp=repr(exp_v), got=repr(got_v)), 60))
                good_cols = len(exp_cols) - n_bad_cols
                score += 60 * good_cols / len(exp_cols) * 0.5
    else:
        items.append(CheckItem("Values", False, t("Values were not compared because the columns or row count do not match yet."), 60))
    return items, round(min(score, 100.0), 1)


def grade_sql(ex: Exercise, code: str, settings: RunSettings) -> GradeResult:
    res = run_sql_many({"user": code, "ref": ex.solution}, settings, search_path=ex.search_path)
    user, ref = res["user"], res["ref"]
    if not ref.ok:
        return GradeResult(False, 0.0, content_error=t("Reference solution failed: {err}", err=ref.error), summary=t("This exercise has a content problem; please report it."))
    if not user.ok:
        nxt = t(user.hint) if user.hint else t("Read the error message: it usually names the clause and the token near the problem.")
        return GradeResult(False, 0.0, summary=t("Your query did not run."), error=user.error, hint=user.hint, next_step=nxt, run=user)
    items, score = compare_result_sets(user.frame, ref.frame, ex.order_matters, ex.float_tol)
    passed = score >= 99.99
    return _finish(GradeResult(passed, score, items, user_frame=user.frame, expected_preview=ref.frame.head(10), run=user), ex)


# ------------------------------------------------------------- Python ------
def grade_python(ex: Exercise, code: str, settings: RunSettings) -> GradeResult:
    run = run_python(code, settings, preload=ex.preload, ref_code=ex.solution,
                     checks=[{"name": c.name, "code": c.code, "hint": c.hint, "weight": c.weight} for c in ex.checks],
                     search_path=ex.search_path)
    if run.ref_error:
        return GradeResult(False, 0.0, content_error=t("Reference solution failed: {err}", err=run.ref_error), summary=t("This exercise has a content problem; please report it."), run=run)
    if run.timed_out or (run.error and not run.checks):
        return GradeResult(False, 0.0, summary=t("Your code did not finish."), error=run.error, next_step=t("Fix the error shown, run again, then submit."), run=run)
    items = [CheckItem(c.name, c.passed, c.message, c.weight) for c in run.checks]
    total = sum(i.weight for i in items) or 1
    score = round(100 * sum(i.weight for i in items if i.passed) / total, 1)
    g = GradeResult(all(i.passed for i in items), score, items, error=run.error, run=run, user_frame=run.result)
    return _finish(g, ex)


# ------------------------------------------------------------------ R ------
def grade_r(ex: Exercise, code: str, settings: RunSettings, rscript: str) -> GradeResult:
    run = run_r(code, rscript, settings, preload=ex.preload, ref_code=ex.solution,
                checks=[{"name": c.name, "code": c.code, "hint": c.hint, "weight": c.weight} for c in ex.checks])
    if run.timed_out or (run.error and not run.checks):
        return GradeResult(False, 0.0, summary=t("Your R code did not finish."), error=run.error, run=run)
    items = []
    for c, chk in zip(run.checks, ex.checks):
        msg = c.message if c.message else ("" if c.passed else chk.hint)
        items.append(CheckItem(c.name, c.passed, msg, c.weight))
    total = sum(i.weight for i in items) or 1
    score = round(100 * sum(i.weight for i in items if i.passed) / total, 1)
    return _finish(GradeResult(all(i.passed for i in items), score, items, error=run.error, run=run), ex)


def _finish(g: GradeResult, ex: Exercise) -> GradeResult:
    failed = [i for i in g.items if not i.passed]
    if g.passed:
        g.summary = t("All checks passed - score {s:.0f}/100.", s=g.score)
        g.next_step = t("Compare your code with the reference solution for alternative approaches, then try the independent challenge.")
    else:
        g.summary = t("{n} of {total} checks passed - score {s:.0f}/100.", n=len(g.items) - len(failed), total=len(g.items), s=g.score)
        first = failed[0]
        g.next_step = t("Focus on '{name}': {msg}", name=t(first.name), msg=first.message or t("see the requirement for this check."))
    return g


def feedback_dict(g: GradeResult) -> dict:
    return {
        "score": g.score,
        "passed": g.passed,
        "summary": g.summary,
        "items": [{"name": i.name, "passed": i.passed, "message": i.message} for i in g.items],
        "error": g.error,
    }
