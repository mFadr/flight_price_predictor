"""Reproducible, locally rendered visualisations.

Specs come either from the tutor model (a ```viz JSON block) or from the UI.
All plotted values are computed here from the spec - the model never supplies
pixel data - and every figure is labelled as illustrative / synthetic /
conceptual where appropriate.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Literal

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from pydantic import BaseModel, Field, ValidationError  # noqa: E402

from tutor.tools.safe_parse import MathParseError, parse_math  # noqa: E402

Kind = Literal[
    "function_plot", "number_line", "supply_demand", "budget_constraint", "ppf", "distribution", "histogram",
    "scatter_regression", "vectors", "motion_graph", "force_diagram", "wave", "flowchart", "array",
]

_VIZ_BLOCK = re.compile(r"```viz\s*(\{.*?\})\s*```", re.S)


class VisualizationSpec(BaseModel):
    kind: Kind
    title: str = ""
    # generic parameters (only those relevant to ``kind`` are used)
    expressions: list[str] = Field(default_factory=list)
    x_min: float | None = None
    x_max: float | None = None
    mark_x: list[float] = Field(default_factory=list)
    points: list[float] = Field(default_factory=list)
    intervals: list[list[float]] = Field(default_factory=list)
    demand: list[float] = Field(default_factory=list)
    supply: list[float] = Field(default_factory=list)
    demand2: list[float] = Field(default_factory=list)
    supply2: list[float] = Field(default_factory=list)
    income: float | None = None
    price_x: float | None = None
    price_y: float | None = None
    max_x: float | None = None
    max_y: float | None = None
    labels: list[str] = Field(default_factory=list)
    dist: str = "normal"
    params: dict[str, float] = Field(default_factory=dict)
    shade: list[float] = Field(default_factory=list)
    data: list[float] = Field(default_factory=list)
    x: list[float] = Field(default_factory=list)
    y: list[float] = Field(default_factory=list)
    n: int | None = None
    mean: float | None = None
    sd: float | None = None
    slope: float | None = None
    intercept: float | None = None
    noise: float | None = None
    vectors: list[list[Any]] = Field(default_factory=list)
    x0: float = 0.0
    v0: float = 0.0
    a: float = 0.0
    t_max: float = 5.0
    forces: list[list[Any]] = Field(default_factory=list)
    amplitude: float = 1.0
    wavelength: float = 1.0
    phase: float = 0.0
    steps: list[str] = Field(default_factory=list)
    values: list[Any] = Field(default_factory=list)
    highlight: list[int] = Field(default_factory=list)


class RenderedViz(BaseModel):
    path: str
    spec: VisualizationSpec
    caption: str
    elements: list[str]   # named parts the student can ask about


class VizError(ValueError):
    pass


def extract_viz_blocks(text: str) -> tuple[str, list[VisualizationSpec], list[str]]:
    """Remove ```viz blocks from ``text``; return cleaned text, valid specs and error notes."""
    specs, errors = [], []
    for m in _VIZ_BLOCK.finditer(text):
        try:
            specs.append(VisualizationSpec.model_validate(json.loads(m.group(1))))
        except (json.JSONDecodeError, ValidationError) as exc:
            errors.append(type(exc).__name__)
    return _VIZ_BLOCK.sub("", text).rstrip(), specs[:1], errors


def _fn(expr_text: str, var: str = "x"):
    expr = parse_math(expr_text)
    syms = sorted(expr.free_symbols, key=str)
    if len(syms) > 1:
        raise VizError(f"'{expr_text}' has more than one variable")
    s = syms[0] if syms else sp.Symbol(var, real=True)
    return sp.lambdify(s, expr, modules=["numpy"]), expr


class VizRenderer:
    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def render(self, spec: VisualizationSpec) -> RenderedViz:
        key = hashlib.sha1(spec.model_dump_json().encode()).hexdigest()[:16]
        fig = Figure(figsize=(6.4, 4.2), dpi=110, layout="tight")
        FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        handler = getattr(self, "_" + spec.kind)
        caption, elements = handler(spec, ax)
        if spec.title:
            ax.set_title(spec.title)
        path = self.out_dir / f"{spec.kind}-{key}.png"
        fig.savefig(path)
        return RenderedViz(path=str(path), spec=spec, caption=caption, elements=elements)

    # ------------------------------------------------------------ maths
    def _function_plot(self, s: VisualizationSpec, ax):
        if not s.expressions:
            raise VizError("function_plot needs 'expressions'")
        lo, hi = s.x_min if s.x_min is not None else -5.0, s.x_max if s.x_max is not None else 5.0
        if hi <= lo:
            lo, hi = hi, lo + 10
        xs = np.linspace(lo, hi, 800)
        elements = []
        for text in s.expressions[:4]:
            f, expr = _fn(text)
            with np.errstate(all="ignore"):
                ys = np.asarray(f(xs), dtype=float) * np.ones_like(xs)
            ys[~np.isfinite(ys)] = np.nan
            if np.nanmax(np.abs(ys)) > 1e6:
                ys[np.abs(ys) > 1e3 * np.nanmedian(np.abs(ys)) + 1] = np.nan  # hide asymptote spikes
            ax.plot(xs, ys, label=f"${sp.latex(expr)}$")
            elements.append(f"curve y = {text}")
            for mx in s.mark_x[:6]:
                with np.errstate(all="ignore"):
                    my = float(f(mx))
                if math.isfinite(my):
                    ax.plot([mx], [my], "o", color="black")
                    ax.annotate(f"({mx:g}, {my:.3g})", (mx, my), textcoords="offset points", xytext=(5, 5))
                    elements.append(f"point ({mx:g}, {my:.3g})")
        ax.axhline(0, color="grey", lw=0.8)
        ax.axvline(0, color="grey", lw=0.8)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.grid(alpha=0.3)
        ax.legend()
        return "Function graph computed exactly from the given expression(s).", elements

    def _number_line(self, s: VisualizationSpec, ax):
        vals = s.points + [v for iv in s.intervals for v in iv[:2]]
        lo = s.x_min if s.x_min is not None else (min(vals) - 2 if vals else -5)
        hi = s.x_max if s.x_max is not None else (max(vals) + 2 if vals else 5)
        ax.axhline(0, color="black", lw=1.5)
        for t in np.arange(math.floor(lo), math.ceil(hi) + 1):
            ax.plot([t, t], [-0.05, 0.05], color="black", lw=1)
            ax.text(t, -0.18, f"{t:g}", ha="center", fontsize=8)
        els = []
        for iv in s.intervals[:4]:
            if len(iv) >= 2:
                ax.plot([iv[0], iv[1]], [0, 0], color="tab:blue", lw=6, alpha=0.5)
                els.append(f"interval [{iv[0]:g}, {iv[1]:g}]")
        for p in s.points[:10]:
            ax.plot([p], [0], "o", color="tab:red", ms=9)
            ax.text(p, 0.12, f"{p:g}", ha="center", color="tab:red")
            els.append(f"point {p:g}")
        ax.set_xlim(lo - 0.5, hi + 0.5)
        ax.set_ylim(-0.5, 0.5)
        ax.axis("off")
        return "Number line.", els

    def _vectors(self, s: VisualizationSpec, ax):
        els, m = [], 1.0
        for i, v in enumerate(s.vectors[:6]):
            x, y = float(v[0]), float(v[1])
            label = str(v[2]) if len(v) > 2 else f"v{i + 1}"
            ax.quiver(0, 0, x, y, angles="xy", scale_units="xy", scale=1, color=f"C{i}")
            ax.text(x, y, f" {label} ({x:g}, {y:g})", color=f"C{i}")
            m = max(m, abs(x), abs(y))
            els.append(f"vector {label} = ({x:g}, {y:g}), length {math.hypot(x, y):.3g}")
        ax.set_xlim(-m * 1.2, m * 1.2)
        ax.set_ylim(-m * 1.2, m * 1.2)
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        ax.axhline(0, color="grey", lw=0.8)
        ax.axvline(0, color="grey", lw=0.8)
        return "Vectors drawn to scale from the origin.", els

    # ------------------------------------------------------------ economics
    def _supply_demand(self, s: VisualizationSpec, ax):
        if len(s.demand) < 2 or len(s.supply) < 2:
            raise VizError("supply_demand needs 'demand' [a, b] and 'supply' [c, d]")
        els = []

        def eq(dm, su):
            a, b = dm[:2]
            c, d = su[:2]
            q = (a - c) / (b + d) if (b + d) else float("nan")
            return q, a - b * q

        curves = [("Demand D", s.demand, -1, "tab:blue", "-"), ("Supply S", s.supply, 1, "tab:orange", "-")]
        if len(s.demand2) >= 2:
            curves.append(("Demand D'", s.demand2, -1, "tab:blue", "--"))
        if len(s.supply2) >= 2:
            curves.append(("Supply S'", s.supply2, 1, "tab:orange", "--"))
        q0, p0 = eq(s.demand, s.supply)
        qmax = max(1.0, 2 * abs(q0) if math.isfinite(q0) else 10)
        qs = np.linspace(0, qmax, 200)
        for name, (i0, sl, *_), sign, col, ls in [(n, c, sg, co, l) for n, c, sg, co, l in curves]:
            ax.plot(qs, i0 + sign * sl * qs, color=col, ls=ls, label=f"{name}: P = {i0:g} {'+' if sign > 0 else '−'} {sl:g}Q")
            els.append(name)
        pts = [("E", q0, p0)]
        if len(s.demand2) >= 2 or len(s.supply2) >= 2:
            q1, p1 = eq(s.demand2 or s.demand, s.supply2 or s.supply)
            pts.append(("E'", q1, p1))
        for lab, q, p in pts:
            if math.isfinite(q) and q >= 0:
                ax.plot([q], [p], "ko")
                ax.plot([q, q], [0, p], "k:", lw=0.8)
                ax.plot([0, q], [p, p], "k:", lw=0.8)
                ax.annotate(f"{lab} (Q={q:.3g}, P={p:.3g})", (q, p), textcoords="offset points", xytext=(6, 6))
                els.append(f"equilibrium {lab}: Q = {q:.3g}, P = {p:.3g}")
        ax.set_xlabel("Quantity Q")
        ax.set_ylabel("Price P")
        ax.set_ylim(bottom=0)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        return "Hypothetical linear supply and demand; equilibrium computed exactly (Qd = Qs).", els

    def _budget_constraint(self, s: VisualizationSpec, ax):
        if not (s.income and s.price_x and s.price_y):
            raise VizError("budget_constraint needs income, price_x, price_y")
        mx, my = s.income / s.price_x, s.income / s.price_y
        ax.plot([0, mx], [my, 0], color="tab:green", label=f"{s.price_x:g}·X + {s.price_y:g}·Y = {s.income:g}")
        ax.fill_between([0, mx], [my, 0], alpha=0.15, color="tab:green")
        ax.set_xlabel(s.labels[0] if s.labels else "Good X")
        ax.set_ylabel(s.labels[1] if len(s.labels) > 1 else "Good Y")
        ax.legend()
        ax.grid(alpha=0.3)
        return (f"Budget line: intercepts X = {mx:.3g}, Y = {my:.3g}; slope = −{s.price_x / s.price_y:.3g} (hypothetical values).",
                ["budget line", "affordable set (shaded)", f"X intercept {mx:.3g}", f"Y intercept {my:.3g}",
                 f"slope −px/py = −{s.price_x / s.price_y:.3g}"])

    def _ppf(self, s: VisualizationSpec, ax):
        mx, my = s.max_x or 100, s.max_y or 100
        t = np.linspace(0, math.pi / 2, 200)
        ax.plot(mx * np.sin(t), my * np.cos(t), color="tab:purple", label="PPF")
        ax.plot([mx * 0.4], [my * 0.4], "o", color="grey")
        ax.annotate("inefficient", (mx * 0.4, my * 0.4), xytext=(5, 5), textcoords="offset points")
        ax.plot([mx * 0.9], [my * 0.9], "x", color="red")
        ax.annotate("unattainable", (mx * 0.9, my * 0.9), xytext=(5, 5), textcoords="offset points")
        ax.set_xlabel(s.labels[0] if s.labels else "Good X")
        ax.set_ylabel(s.labels[1] if len(s.labels) > 1 else "Good Y")
        ax.grid(alpha=0.3)
        return "Conceptual production possibility frontier (bowed out = increasing opportunity cost); not to scale.", \
            ["frontier (efficient points)", "inefficient point inside", "unattainable point outside"]

    # ------------------------------------------------------------ statistics
    def _distribution(self, s: VisualizationSpec, ax):
        d, p = s.dist.lower(), s.params
        els = []
        if d == "normal":
            mu, sig = p.get("mu", p.get("mean", 0.0)), p.get("sigma", p.get("sd", 1.0))
            xs = np.linspace(mu - 4 * sig, mu + 4 * sig, 400)
            ys = np.exp(-((xs - mu) ** 2) / (2 * sig**2)) / (sig * math.sqrt(2 * math.pi))
            ax.plot(xs, ys)
            if len(s.shade) == 2:
                a, b = s.shade
                m = (xs >= a) & (xs <= b)
                ax.fill_between(xs[m], ys[m], alpha=0.3)
                prob = 0.5 * (math.erf((b - mu) / (sig * math.sqrt(2))) - math.erf((a - mu) / (sig * math.sqrt(2))))
                els.append(f"shaded area P({a:g} ≤ X ≤ {b:g}) = {prob:.4f}")
            ax.set_ylabel("density")
            els += [f"mean μ = {mu:g}", f"standard deviation σ = {sig:g}"]
            cap = f"Normal distribution N({mu:g}, {sig:g}²); probabilities computed exactly."
        elif d in ("binomial", "poisson"):
            if d == "binomial":
                n, pr = int(p.get("n", 10)), p.get("p", 0.5)
                ks = np.arange(0, n + 1)
                ys = np.array([math.comb(n, k) * pr**k * (1 - pr) ** (n - k) for k in ks])
                cap = f"Binomial(n={n}, p={pr:g}); mean = {n * pr:.3g}."
            else:
                lam = p.get("lambda", p.get("lam", 3.0))
                ks = np.arange(0, int(lam * 3 + 10))
                ys = np.array([math.exp(-lam) * lam**k / math.factorial(k) for k in ks])
                cap = f"Poisson(λ={lam:g}); mean = variance = {lam:g}."
            colors = ["tab:orange" if len(s.shade) == 2 and s.shade[0] <= k <= s.shade[1] else "tab:blue" for k in ks]
            ax.bar(ks, ys, color=colors)
            ax.set_ylabel("P(X = k)")
            if len(s.shade) == 2:
                els.append(f"highlighted P({s.shade[0]:g} ≤ X ≤ {s.shade[1]:g}) = {ys[(ks >= s.shade[0]) & (ks <= s.shade[1])].sum():.4f}")
            els.append("probability bars")
        elif d == "uniform":
            a, b = p.get("a", 0.0), p.get("b", 1.0)
            ax.plot([a - 1, a, a, b, b, b + 1], [0, 0, 1 / (b - a), 1 / (b - a), 0, 0])
            cap = f"Uniform({a:g}, {b:g}); density = 1/(b−a) = {1 / (b - a):.3g}."
            els.append("constant density")
        else:
            raise VizError(f"unknown distribution '{s.dist}'")
        ax.set_xlabel("x")
        ax.grid(alpha=0.3)
        return cap, els

    def _histogram(self, s: VisualizationSpec, ax):
        if s.data:
            data, src = np.asarray(s.data, dtype=float), "Your data"
        else:
            rng = np.random.default_rng(42)
            data = rng.normal(s.mean or 50, s.sd or 10, int(min(s.n or 200, 5000)))
            src = "SYNTHETIC data (randomly generated for illustration)"
        ax.hist(data, bins="auto", color="tab:blue", alpha=0.7, edgecolor="white")
        mean, med = float(np.mean(data)), float(np.median(data))
        ax.axvline(mean, color="red", label=f"mean = {mean:.3g}")
        ax.axvline(med, color="green", ls="--", label=f"median = {med:.3g}")
        ax.set_xlabel("value")
        ax.set_ylabel("frequency")
        ax.legend()
        sd = float(np.std(data, ddof=1)) if len(data) > 1 else 0.0
        return f"{src}; n = {len(data)}, sample SD = {sd:.3g}.", ["bars (frequencies)", f"mean {mean:.3g}", f"median {med:.3g}"]

    def _scatter_regression(self, s: VisualizationSpec, ax):
        if s.x and s.y and len(s.x) == len(s.y):
            x, y, src = np.asarray(s.x, float), np.asarray(s.y, float), "Your data"
        else:
            rng = np.random.default_rng(7)
            n = int(min(s.n or 40, 2000))
            x = rng.uniform(0, 10, n)
            y = (s.intercept or 1.0) + (s.slope if s.slope is not None else 2.0) * x + rng.normal(0, s.noise or 2.0, n)
            src = "SYNTHETIC data (randomly generated for illustration)"
        if len(x) < 2:
            raise VizError("need at least 2 points")
        b1, b0 = np.polyfit(x, y, 1)
        r = float(np.corrcoef(x, y)[0, 1])
        ax.scatter(x, y, alpha=0.7)
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, b0 + b1 * xs, color="red", label=f"ŷ = {b0:.3g} + {b1:.3g}x")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()
        ax.grid(alpha=0.3)
        return (f"{src}; least-squares line computed with NumPy, r = {r:.3f}, R² = {r * r:.3f}. Correlation does not imply causation.",
                ["data points", f"regression line slope {b1:.3g}", f"intercept {b0:.3g}", f"correlation r = {r:.3f}"])

    # ------------------------------------------------------------ physics
    def _motion_graph(self, s: VisualizationSpec, ax):
        t = np.linspace(0, s.t_max or 5, 200)
        x = s.x0 + s.v0 * t + 0.5 * s.a * t**2
        v = s.v0 + s.a * t
        ax.plot(t, x, label="position x(t) [m]")
        ax2 = ax.twinx()
        ax2.plot(t, v, color="tab:orange", ls="--", label="velocity v(t) [m/s]")
        ax.set_xlabel("time t [s]")
        ax.set_ylabel("position [m]")
        ax2.set_ylabel("velocity [m/s]")
        ax.legend(loc="upper left")
        ax2.legend(loc="lower right")
        ax.grid(alpha=0.3)
        return (f"Constant acceleration: x = {s.x0:g} + {s.v0:g}t + ½·{s.a:g}t², v = {s.v0:g} + {s.a:g}t.",
                ["position curve (slope = velocity)", "velocity line (slope = acceleration)"])

    def _force_diagram(self, s: VisualizationSpec, ax):
        from matplotlib.patches import Rectangle
        ax.add_patch(Rectangle((-0.5, -0.5), 1, 1, color="lightgrey", ec="black"))
        els = []
        mags = [abs(float(f[2])) for f in s.forces if len(f) >= 3] or [1]
        mmax = max(mags) or 1
        for i, f in enumerate(s.forces[:8]):
            label, ang = str(f[0]), math.radians(float(f[1]))
            mag = float(f[2]) if len(f) >= 3 else 1.0
            L = 0.6 + 1.4 * abs(mag) / mmax
            dx, dy = L * math.cos(ang), L * math.sin(ang)
            ax.annotate("", xy=(dx, dy), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=2, color=f"C{i}"))
            ax.text(dx * 1.1, dy * 1.1, f"{label}\n{mag:g}", ha="center", color=f"C{i}")
            els.append(f"force {label}: {mag:g} at {float(f[1]):g}°")
        fx = sum(float(f[2]) * math.cos(math.radians(float(f[1]))) for f in s.forces if len(f) >= 3)
        fy = sum(float(f[2]) * math.sin(math.radians(float(f[1]))) for f in s.forces if len(f) >= 3)
        els.append(f"net force ≈ ({fx:.3g}, {fy:.3g}), magnitude {math.hypot(fx, fy):.3g}")
        ax.set_xlim(-2.5, 2.5)
        ax.set_ylim(-2.5, 2.5)
        ax.set_aspect("equal")
        ax.axis("off")
        return "Free-body diagram - CONCEPTUAL, arrow lengths only roughly proportional; net force computed from the numbers.", els

    def _wave(self, s: VisualizationSpec, ax):
        x = np.linspace(0, 3 * (s.wavelength or 1), 600)
        y = s.amplitude * np.sin(2 * math.pi * x / (s.wavelength or 1) + s.phase)
        ax.plot(x, y)
        ax.annotate("", xy=(s.wavelength, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="<->"))
        ax.text(s.wavelength / 2, 0.08 * s.amplitude, f"λ = {s.wavelength:g}", ha="center")
        ax.axhline(s.amplitude, color="grey", ls=":")
        ax.text(0, s.amplitude * 1.05, f"A = {s.amplitude:g}")
        ax.set_xlabel("position x")
        ax.set_ylabel("displacement y")
        ax.grid(alpha=0.3)
        return "Sinusoidal wave y = A·sin(2πx/λ + φ).", ["amplitude A", "wavelength λ", "phase φ"]

    # ------------------------------------------------------------ programming
    def _flowchart(self, s: VisualizationSpec, ax):
        steps = s.steps[:10] or ["start", "end"]
        n = len(steps)
        for i, st in enumerate(steps):
            y = n - i
            decision = st.strip().endswith("?")
            box = dict(boxstyle="round,pad=0.4" if not decision else "darrow,pad=0.3",
                       fc="#fff4d6" if decision else "#dde9ff", ec="black")
            ax.text(0, y, st[:60], ha="center", va="center", bbox=box, fontsize=9)
            if i < n - 1:
                ax.annotate("", xy=(0, y - 0.7), xytext=(0, y - 0.3), arrowprops=dict(arrowstyle="->"))
        ax.set_xlim(-3, 3)
        ax.set_ylim(0.3, n + 0.7)
        ax.axis("off")
        return "Flowchart (conceptual).", [f"step {i + 1}: {st}" for i, st in enumerate(steps)]

    def _array(self, s: VisualizationSpec, ax):
        from matplotlib.patches import Rectangle
        vals = s.values[:20]
        for i, v in enumerate(vals):
            hl = i in s.highlight
            ax.add_patch(Rectangle((i, 0), 1, 1, fc="#ffd27f" if hl else "#e8eef7", ec="black"))
            ax.text(i + 0.5, 0.5, str(v)[:6], ha="center", va="center")
            ax.text(i + 0.5, -0.3, str(i), ha="center", fontsize=8, color="grey")
        ax.set_xlim(-0.2, max(1, len(vals)) + 0.2)
        ax.set_ylim(-0.6, 1.4)
        ax.set_aspect("equal")
        ax.axis("off")
        return "Array with indices (highlighted cells in orange).", [f"index {i}: {v}" for i, v in enumerate(vals)]


def safe_render(renderer: VizRenderer, spec: VisualizationSpec) -> tuple[RenderedViz | None, str]:
    try:
        return renderer.render(spec), ""
    except (VizError, MathParseError, ValueError, TypeError, IndexError, ZeroDivisionError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
