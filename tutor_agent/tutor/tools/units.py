"""Physical quantities: parse "12.5 m/s^2", check dimensions and compare values."""

from __future__ import annotations

import math
import re

import sympy as sp
from sympy.physics import units as u
from sympy.physics.units import convert_to

from tutor.domain import VerificationResult, VerificationStatus
from tutor.tools.safe_parse import MathParseError, normalise, to_number

V = VerificationStatus

UNITS: dict[str, sp.Expr] = {
    "m": u.meter, "km": u.kilometer, "cm": u.centimeter, "mm": u.millimeter, "um": u.micrometer, "nm": u.nanometer,
    "s": u.second, "ms": u.millisecond, "min": u.minute, "h": u.hour,
    "kg": u.kilogram, "g": u.gram, "mg": u.milligram,
    "N": u.newton, "kN": 1000 * u.newton, "J": u.joule, "kJ": 1000 * u.joule, "eV": u.electronvolt,
    "W": u.watt, "kW": 1000 * u.watt, "Pa": u.pascal, "kPa": 1000 * u.pascal, "bar": u.bar, "atm": u.atmosphere,
    "V": u.volt, "A": u.ampere, "mA": u.ampere / 1000, "ohm": u.ohm, "Ω": u.ohm, "C": u.coulomb, "F": u.farad,
    "T": u.tesla, "Hz": u.hertz, "kHz": 1000 * u.hertz, "K": u.kelvin, "mol": u.mole, "L": u.liter, "l": u.liter,
    "rad": u.radian,
}
_BASE = [u.meter, u.kilogram, u.second, u.ampere, u.kelvin, u.mole, u.candela]
_SPLIT = re.compile(r"^\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:\s*(?:[eE][-+]?\d+|[*x×·]\s*10\s*\^\s*[-+]?\d+))?)\s*(.*)$")
_UNIT_TOKEN = re.compile(r"[A-Za-zΩ]+|\d+|[*/^()·\s.-]")


def parse_unit(text: str) -> sp.Expr:
    text = text.strip().replace("·", "*").replace("²", "^2").replace("³", "^3")
    if not text:
        return sp.Integer(1)
    pos, out = 0, []
    while pos < len(text):
        m = _UNIT_TOKEN.match(text, pos)
        if not m:
            raise MathParseError(f"Unknown unit syntax near {text[pos:pos+6]!r}")
        tok = m.group(0)
        if tok.isalpha() or tok == "Ω":
            if tok not in UNITS:
                raise MathParseError(f"Unknown unit '{tok}'")
            out.append(f"U['{tok}']")
        elif tok == "^":
            out.append("**")
        elif tok == ".":
            out.append("*")
        elif tok.strip():
            out.append(tok)
        pos = m.end()
    expr_src = "".join(out)
    # implicit multiplication between adjacent units: "N m" / "kg m"
    expr_src = re.sub(r"\]\s*U\[", "]*U[", expr_src)
    try:
        return eval(expr_src, {"__builtins__": {}}, {"U": UNITS})  # noqa: S307 - tokens whitelisted above
    except Exception as exc:
        raise MathParseError(f"Could not interpret unit '{text}'") from exc


def parse_quantity(text: str) -> sp.Expr:
    text = normalise(text)
    if "=" in text:
        text = text.split("=")[-1]
    m = _SPLIT.match(text)
    if not m:
        raise MathParseError("Expected a number followed by a unit, e.g. '9.8 m/s^2'")
    num_s, unit_s = m.group(1), m.group(2)
    num_s = re.sub(r"[x×·]\s*10", "*10", num_s.replace(" ", ""))
    return to_number(num_s) * parse_unit(unit_s)


def _si(q: sp.Expr) -> sp.Expr:
    return convert_to(q, _BASE)


def same_dimension(a: sp.Expr, b: sp.Expr) -> bool:
    ratio = sp.simplify(_si(a) / _si(b))
    return not ratio.free_symbols and not ratio.has(*_BASE) and ratio.is_number


def check_quantity(student: str, expected: str, rel_tol: float = 1e-3) -> VerificationResult:
    method = f"Unit-aware comparison (SymPy units, tolerance {rel_tol:g})"
    try:
        s, e = parse_quantity(student), parse_quantity(expected)
    except MathParseError as exc:
        return VerificationResult(status=V.PARSE_ERROR, method=method, details=str(exc))
    s_has_unit = any(isinstance(x, u.Quantity) for x in s.atoms(u.Quantity))
    e_has_unit = any(isinstance(x, u.Quantity) for x in e.atoms(u.Quantity))
    if e_has_unit and not s_has_unit:
        return VerificationResult(status=V.INCORRECT, method=method, details="The answer has no unit; a unit is required.",
                                  data={"units_missing": True})
    if not same_dimension(s, e):
        return VerificationResult(status=V.INCORRECT, method=method,
                                  details="The unit has the wrong dimension (e.g. a speed was expected but something else was given).",
                                  data={"dimension_mismatch": True})
    ratio = float(sp.N(sp.simplify(_si(s) / _si(e))))
    if math.isclose(ratio, 1.0, rel_tol=rel_tol):
        return VerificationResult(status=V.CORRECT, method=method, details="Value and dimension are consistent.")
    detail = "Dimension is correct, but the value differs."
    if math.isclose(ratio, -1.0, rel_tol=rel_tol):
        detail += " The sign is opposite."
    return VerificationResult(status=V.INCORRECT, method=method, details=detail, data={"ratio": ratio})
