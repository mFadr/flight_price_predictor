"""Deterministic mathematical verification (SymPy + numeric sampling).

Results always state the method used and its limitations - the application
never claims a verification it did not perform.
"""

from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass
from functools import lru_cache

import sympy as sp

from tutor.domain import VerificationResult, VerificationStatus
from tutor.tools.safe_parse import MathParseError, normalise, parse_equation, parse_math, to_number

V = VerificationStatus


# ------------------------------------------------------------------ expressions

@lru_cache(maxsize=1024)
def _equivalent(a: str, b: str) -> tuple[str, str]:
    ea, eb = parse_math(a), parse_math(b)
    try:
        diff = sp.simplify(ea - eb)
        if diff == 0:
            return "equivalent", "SymPy simplified the difference to 0."
    except Exception:
        pass
    # numeric sampling fallback
    syms = sorted(ea.free_symbols | eb.free_symbols, key=str)
    rng = random.Random(1234)
    ok = tested = 0
    for _ in range(12):
        subs = {s: rng.uniform(0.3, 2.7) for s in syms}
        try:
            va, vb = complex(sp.N(ea.subs(subs))), complex(sp.N(eb.subs(subs)))
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        if not all(map(math.isfinite, (va.real, va.imag, vb.real, vb.imag))):
            continue
        tested += 1
        if abs(va - vb) <= 1e-8 * max(1.0, abs(va), abs(vb)):
            ok += 1
        else:
            return "different", f"They differ, e.g. at {', '.join(f'{k}={v:.3g}' for k, v in subs.items())}: {va.real:.6g} vs {vb.real:.6g}."
    if tested >= 5 and ok == tested:
        return "likely", f"Not proven symbolically, but equal at {tested} random sample points."
    return "unknown", "Could not decide equivalence symbolically or numerically."


def check_expression(student: str, expected: str) -> VerificationResult:
    method = "SymPy symbolic equivalence (numeric sampling as fallback)"
    try:
        verdict, detail = _equivalent(student.strip(), expected.strip())
    except MathParseError as exc:
        return VerificationResult(status=V.PARSE_ERROR, method=method, details=str(exc))
    status = {"equivalent": V.CORRECT, "likely": V.CORRECT, "different": V.INCORRECT, "unknown": V.UNVERIFIABLE}[verdict]
    return VerificationResult(status=status, method=method, details=detail, data={"verdict": verdict})


# ------------------------------------------------------------------ numbers

def check_numeric(student: str, expected: str, rel_tol: float = 1e-6, abs_tol: float = 1e-9) -> VerificationResult:
    method = f"Numeric comparison (relative tolerance {rel_tol:g})"
    try:
        s = to_number(_strip_lhs(student))
        e = to_number(_strip_lhs(expected))
    except MathParseError as exc:
        return VerificationResult(status=V.PARSE_ERROR, method=method, details=str(exc))
    if math.isclose(s, e, rel_tol=max(rel_tol, 1e-12), abs_tol=abs_tol):
        return VerificationResult(status=V.CORRECT, method=method, details=f"{s:.6g} matches {e:.6g}.")
    detail = f"{s:.6g} differs from the expected value."
    if e != 0 and math.isclose(s, -e, rel_tol=max(rel_tol, 1e-12)):
        detail += " The magnitude is right but the sign is opposite."
    elif e != 0 and s != 0:
        ratio = s / e
        for k in (10, 100, 1000):
            if math.isclose(ratio, k, rel_tol=1e-6) or math.isclose(ratio, 1 / k, rel_tol=1e-6):
                detail += f" It is off by a factor of {k} - check units or decimal places."
                break
    return VerificationResult(status=V.INCORRECT, method=method, details=detail, data={"student": s})


def _strip_lhs(text: str) -> str:
    """'x = 4' -> '4' (keeps plain numbers untouched)."""
    text = normalise(text)
    if "=" in text:
        text = text.split("=")[-1]
    return text


# ------------------------------------------------------------------ solution sets

_SPLIT = re.compile(r"\s*(?:,|;|\bor\b|\band\b|\n)\s*", re.I)


def parse_solution_set(text: str, variable: str = "x") -> set[sp.Expr]:
    text = normalise(text)
    text = re.sub(r"[{}\[\]]", " ", text).replace("(", " ( ").replace(")", " ) ")
    text = re.sub(r"\b%s\s*(?:∈|in)\b" % re.escape(variable), " ", text)
    parts = [p for p in _SPLIT.split(text) if p.strip()]
    values: set[sp.Expr] = set()
    for part in parts:
        part = part.strip()
        if "=" in part:
            part = part.split("=")[-1]
        if part.lower() in ("none", "no solution", "∅"):
            continue
        values.add(sp.nsimplify(parse_math(part), rational=False))
    return values


def _same_set(a: set[sp.Expr], b: set[sp.Expr]) -> tuple[bool, list[sp.Expr], list[sp.Expr]]:
    missing = [x for x in b if not any(sp.simplify(x - y) == 0 for y in a)]
    extra = [y for y in a if not any(sp.simplify(x - y) == 0 for x in b)]
    return not missing and not extra, missing, extra


def check_solutions(student: str, expected: str, variable: str = "x") -> VerificationResult:
    method = "SymPy comparison of solution sets"
    try:
        s = parse_solution_set(student, variable)
        e = parse_solution_set(expected, variable)
    except MathParseError as exc:
        return VerificationResult(status=V.PARSE_ERROR, method=method, details=str(exc))
    same, missing, extra = _same_set(s, e)
    if same:
        return VerificationResult(status=V.CORRECT, method=method, details="All solutions found, no extra values.")
    found = len(e) - len(missing)
    if found and not extra:
        return VerificationResult(
            status=V.PARTIAL, method=method, score=found / max(1, len(e)),
            details=f"{found} of {len(e)} solutions found; at least one solution is missing.",
        )
    details = []
    if extra:
        details.append(f"{len(extra)} value(s) given are not solutions")
    if missing:
        details.append(f"{len(missing)} solution(s) missing")
    return VerificationResult(status=V.INCORRECT, method=method, details="; ".join(details) + ".",
                              score=found / max(1, len(e)))


def verify_equation_solutions(equation: str, values: str, variable: str = "x") -> VerificationResult:
    """Check that ``values`` are exactly the real solutions of ``equation`` (used to validate generated exercises)."""
    method = "SymPy solveset over the reals"
    try:
        eq = parse_equation(equation)
        sym = sp.Symbol(variable, real=True)
        sol = sp.solveset(eq.lhs - eq.rhs, sym, domain=sp.S.Reals)
        claimed = parse_solution_set(values, variable)
    except (MathParseError, Exception) as exc:
        return VerificationResult(status=V.UNVERIFIABLE, method=method, details=f"Could not solve: {type(exc).__name__}")
    if not isinstance(sol, sp.FiniteSet):
        return VerificationResult(status=V.UNVERIFIABLE, method=method, details=f"Solution set is not finite: {sol}")
    same, _, _ = _same_set(claimed, set(sol))
    return VerificationResult(
        status=V.CORRECT if same else V.INCORRECT, method=method,
        details=f"Solutions of the equation: {sorted(map(str, sol))}", data={"solutions": [str(x) for x in sol]},
    )


# ------------------------------------------------------------------ step chains

@dataclass
class StepCheck:
    index: int            # 0-based line index of the step being checked
    text: str
    ok: bool | None       # None = could not be checked
    note: str


_ARROWS = re.compile(r"\s*(?:=>|⇒|→|->|\n|⟹|\bso\b|\bthen\b|\bhence\b|\btherefore\b)\s*", re.I)


def split_steps(work: str) -> list[str]:
    return [s.strip().rstrip(".") for s in _ARROWS.split(work) if s and s.strip()]


def _solution_set(eq: sp.Eq):
    syms = sorted(eq.free_symbols, key=str)
    if len(syms) != 1:
        return None, syms
    return sp.solveset(eq.lhs - eq.rhs, syms[0], domain=sp.S.Reals), syms


def check_steps(work: str) -> list[StepCheck]:
    """Verify a chain of equation transformations or expression rewrites.

    For equations, each step must keep the same real solution set as the
    previous one. For expression chains (``a = b = c`` or one expression per
    line), consecutive expressions must be equivalent. Returns one entry per
    step; the first ``ok is False`` is the earliest detectable error.
    """
    steps = split_steps(work)
    out: list[StepCheck] = []
    if not steps:
        return out
    # Single line with several '=' -> expression chain
    if len(steps) == 1 and normalise(steps[0]).count("=") >= 2:
        steps = [s for s in normalise(steps[0]).split("=") if s.strip()]
    is_eq = all(normalise(s).count("=") == 1 for s in steps)
    prev = None
    for i, step in enumerate(steps):
        try:
            if is_eq:
                cur = _solution_set(parse_equation(step))
                if prev is None:
                    out.append(StepCheck(i, step, True, "starting equation"))
                else:
                    (ps, psyms), (cs, csyms) = prev, cur
                    if ps is None or cs is None:
                        out.append(StepCheck(i, step, None, "several variables - cannot compare solution sets"))
                    elif ps == cs:
                        out.append(StepCheck(i, step, True, "same solutions as the previous step"))
                    else:
                        out.append(StepCheck(i, step, False, f"solution set changed: {ps} → {cs}"))
                prev = cur
            else:
                expr = parse_math(step)
                if prev is None:
                    out.append(StepCheck(i, step, True, "starting expression"))
                else:
                    verdict, detail = _equivalent(str(prev), str(expr))
                    ok = {"equivalent": True, "likely": True, "different": False}.get(verdict)
                    out.append(StepCheck(i, step, ok, detail))
                prev = expr
        except MathParseError as exc:
            out.append(StepCheck(i, step, None, f"not checkable: {exc}"))
            prev = None
    return out


def earliest_error(checks: list[StepCheck]) -> StepCheck | None:
    return next((c for c in checks if c.ok is False), None)


def format_step_report(checks: list[StepCheck]) -> str:
    if not checks:
        return "No checkable mathematical steps were found."
    lines = []
    for c in checks:
        mark = "✔" if c.ok else ("✘" if c.ok is False else "?")
        lines.append(f"{mark} Step {c.index + 1}: `{c.text}` - {c.note}")
    return "\n".join(lines)
