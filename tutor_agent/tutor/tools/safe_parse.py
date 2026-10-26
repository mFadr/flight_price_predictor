"""Safe parsing of untrusted math input into SymPy objects.

``sympy.parse_expr`` evaluates Python code, so all input is first tokenised
against a strict whitelist: numbers, operators, brackets and identifiers made
only of letters/digits that are either known math functions or plain symbol
names. Attribute access, strings, dunders, lambdas etc. are rejected before
SymPy ever sees the text.
"""

from __future__ import annotations

import re
from functools import lru_cache

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

MAX_LEN = 500

FUNCTIONS: dict[str, object] = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "cot": sp.cot, "sec": sp.sec, "csc": sp.csc,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "exp": sp.exp, "log": sp.log, "ln": sp.log, "sqrt": sp.sqrt, "abs": sp.Abs, "Abs": sp.Abs,
    "factorial": sp.factorial, "binomial": sp.binomial, "floor": sp.floor, "ceil": sp.ceiling,
    "ceiling": sp.ceiling, "root": sp.root, "gamma": sp.gamma,
}
CONSTANTS: dict[str, object] = {"pi": sp.pi, "e": sp.E, "E": sp.E, "oo": sp.oo, "inf": sp.oo, "infinity": sp.oo, "i": sp.I, "I": sp.I}
GREEK = {
    "alpha", "beta", "gamma_", "delta", "epsilon", "theta", "lambda_", "mu", "nu", "rho", "sigma",
    "tau", "phi", "omega", "kappa", "eta", "zeta", "xi", "chi", "psi",
}

_TOKEN = re.compile(
    r"\s*(?:(?P<num>\d+(?:\.\d*)?(?:[eE][-+]?\d+)?|\.\d+)|(?P<name>[A-Za-z][A-Za-z0-9_]*)|(?P<op>\*\*|[-+*/^(),=<>!]|\[|\]))"
)
_UNICODE = {"−": "-", "×": "*", "·": "*", "÷": "/", "²": "^2", "³": "^3", "√": "sqrt", "π": "pi", "≤": "<=", "≥": ">=", "∞": "oo"}


class MathParseError(ValueError):
    pass


def normalise(text: str) -> str:
    for k, v in _UNICODE.items():
        text = text.replace(k, v)
    text = text.replace("$", "").replace("\\cdot", "*").replace("\\times", "*")
    text = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"((\1)/(\2))", text)
    text = re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", text)
    text = text.replace("\\left", "").replace("\\right", "").replace("{", "(").replace("}", ")")
    text = re.sub(r"\\(pi|sin|cos|tan|ln|log|exp|theta|alpha|beta)", r"\1", text)
    return text.strip()


def tokenize(text: str) -> list[tuple[str, str]]:
    pos, out = 0, []
    text = text.rstrip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise MathParseError(f"Unsupported character near: {text[pos:pos + 10]!r}")
        kind = m.lastgroup or ""
        val = m.group(kind)
        if kind == "name":
            if "__" in val or len(val) > 12:
                raise MathParseError(f"Unsupported name: {val!r}")
        out.append((kind, val))
        pos = m.end()
    return out


@lru_cache(maxsize=512)
def parse_math(text: str) -> sp.Expr:
    """Parse a single expression (no '=')."""
    text = normalise(text)
    if not text:
        raise MathParseError("Empty expression")
    if len(text) > MAX_LEN:
        raise MathParseError("Expression too long")
    tokens = tokenize(text)
    local: dict[str, object] = {}
    for kind, val in tokens:
        if kind == "name":
            if val in FUNCTIONS:
                local[val] = FUNCTIONS[val]
            elif val in CONSTANTS:
                local[val] = CONSTANTS[val]
            else:
                local[val] = sp.Symbol(val.rstrip("_"), real=True) if val in GREEK or len(val) > 1 else sp.Symbol(val, real=True)
        if kind == "op" and val in ("=", "<", ">", "!"):
            raise MathParseError("Expected an expression, found a relation symbol")
    try:
        expr = parse_expr(
            text,
            local_dict=local,
            transformations=standard_transformations + (implicit_multiplication_application, convert_xor),
            evaluate=True,
        )
    except Exception as exc:  # SymPy raises many types
        raise MathParseError(f"Could not interpret expression: {type(exc).__name__}") from exc
    if not isinstance(expr, sp.Basic):
        raise MathParseError("Not a mathematical expression")
    return expr


def parse_equation(text: str) -> sp.Eq:
    text = normalise(text)
    if text.count("=") != 1 or any(op in text for op in ("<=", ">=", "==", "!=")):
        raise MathParseError("Expected exactly one '=' in the equation")
    lhs, rhs = text.split("=")
    return sp.Eq(parse_math(lhs), parse_math(rhs), evaluate=False)


def to_number(text: str) -> float:
    expr = parse_math(text)
    if expr.free_symbols:
        raise MathParseError("Expected a number, found variables: " + ", ".join(sorted(map(str, expr.free_symbols))))
    val = complex(sp.N(expr))
    if abs(val.imag) > 1e-12:
        raise MathParseError("Complex numbers are not supported here")
    return val.real
