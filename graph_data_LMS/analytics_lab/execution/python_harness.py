"""Child-process harness for learner Python code.

This file is executed as a standalone script (``python -I python_harness.py``)
in a temporary working directory. It must not import ``analytics_lab``.

Protocol: a JSON job arrives on stdin; the harness prints ``<nonce><json>`` as
its final line on the real stdout. Learner output is captured separately.

This is process isolation for robustness (crashes, infinite loops, memory
blow-ups), NOT a security sandbox. See README "Execution safety".
"""

import contextlib
import io
import json
import math
import os
import sys
import time
import traceback

os.environ.setdefault("MPLBACKEND", "Agg")

USER_FILE = "<your code>"
REF_FILE = "<reference>"


def _short_traceback(exc: BaseException, filename: str, source: str = "") -> str:
    """Keep only frames from the learner's code so the error is easy to read."""
    tb = traceback.extract_tb(exc.__traceback__)
    frames = [f for f in tb if f.filename == filename]
    src = source.splitlines()
    lines = []
    for f in frames[-3:]:
        text = src[f.lineno - 1].strip() if f.lineno and 0 < f.lineno <= len(src) else ""
        lines.append(f"  line {f.lineno}: {text}".rstrip())
    msg = "".join(traceback.format_exception_only(type(exc), exc)).strip()
    return ("Traceback (most recent call last, your code only):\n" + "\n".join(lines) + "\n" if lines else "") + msg


def _jsonable(v):
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        return None if math.isnan(v) or math.isinf(v) else v
    try:
        import numpy as np

        if isinstance(v, np.generic):
            return _jsonable(v.item())
    except Exception:
        pass
    return str(v)


def main() -> None:
    job = json.loads(sys.stdin.read())
    nonce = job.pop("nonce")
    real_stdout = sys.stdout
    payload = {"ok": True, "stdout": "", "stderr": "", "error": None, "checks": [], "figures": [],
               "result": None, "variables": [], "ref_error": None, "duration": 0.0}

    import numpy as np
    import pandas as pd
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    db_path = job.get("db_path")
    _cache = {}

    def sql(query: str) -> "pd.DataFrame":
        """Run a read-only DuckDB query against the lab warehouse and return a DataFrame."""
        import duckdb

        con = duckdb.connect(db_path, read_only=True)
        try:
            if job.get("search_path"):
                con.execute(f"SET search_path = '{job['search_path']}'")
            return con.execute(query).df()
        finally:
            con.close()

    def load_table(name: str) -> "pd.DataFrame":
        """Load a table such as 'retail.orders' as a pandas DataFrame (a fresh copy)."""
        if name not in _cache:
            schema, _, table = name.partition(".")
            if not (schema.isidentifier() and table.isidentifier()):
                raise ValueError("Use the form 'schema.table', e.g. load_table('retail.orders')")
            _cache[name] = sql(f'SELECT * FROM "{schema}"."{table}"')
        return _cache[name].copy()

    def make_ns() -> dict:
        ns = {"__name__": "__main__", "pd": pd, "np": np, "plt": plt, "sql": sql, "load_table": load_table}
        for var, table in (job.get("preload") or {}).items():
            ns[var] = load_table(table)
        return ns

    preload_names = set((job.get("preload") or {}).keys()) | {"pd", "np", "plt", "sql", "load_table", "__name__", "__builtins__"}

    # ---- reference solution (grading mode only) -------------------------------------
    ref_ns = None
    if job.get("ref_code"):
        ref_ns = make_ns()
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                exec(compile(job["ref_code"], REF_FILE, "exec"), ref_ns)
        except Exception as exc:  # a broken reference is a content bug; surface it clearly
            payload["ref_error"] = _short_traceback(exc, REF_FILE, job["ref_code"])
        plt.close("all")

    # ---- learner code ----------------------------------------------------------------
    user_ns = make_ns()
    out, err = io.StringIO(), io.StringIO()
    start = time.perf_counter()
    try:
        code = compile(job["user_code"], USER_FILE, "exec")
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exec(code, user_ns)
    except SyntaxError as exc:
        payload["ok"] = False
        payload["error"] = f"SyntaxError on line {exc.lineno}: {exc.msg}\n  {(exc.text or '').rstrip()}"
    except BaseException as exc:  # includes SystemExit / KeyboardInterrupt from learner code
        payload["ok"] = False
        payload["error"] = _short_traceback(exc, USER_FILE, job["user_code"])
    payload["duration"] = round(time.perf_counter() - start, 3)
    max_chars = int(job.get("max_chars", 20000))
    payload["stdout"] = out.getvalue()[:max_chars]
    payload["stderr"] = err.getvalue()[:max_chars]

    # ---- figures ---------------------------------------------------------------------
    figs = [plt.figure(n) for n in plt.get_fignums()]
    out_dir = job.get("out_dir", ".")
    for i, fig in enumerate(figs[:8]):
        path = os.path.join(out_dir, f"figure_{i + 1}.png")
        try:
            fig.savefig(path, dpi=100, bbox_inches="tight")
            payload["figures"].append(os.path.basename(path))
        except Exception as exc:
            payload["stderr"] += f"\n[could not render figure {i + 1}: {exc}]"

    # ---- result preview & variable list ---------------------------------------------
    res = user_ns.get("result")
    max_rows = int(job.get("max_rows", 1000))
    if isinstance(res, pd.Series):
        res = res.to_frame()
    if isinstance(res, pd.DataFrame):
        payload["result"] = {"kind": "frame", "data": res.head(max_rows).to_json(orient="split", date_format="iso", default_handler=str),
                             "shape": list(res.shape)}
    elif res is not None:
        payload["result"] = {"kind": "value", "repr": repr(res)[:2000]}
    for name, val in user_ns.items():
        if name in preload_names or name.startswith("_") or type(val).__name__ in ("module", "function", "type"):
            continue
        shape = getattr(val, "shape", None)
        payload["variables"].append({"name": name, "type": type(val).__name__, "shape": list(shape) if isinstance(shape, tuple) else None})

    # ---- checks ----------------------------------------------------------------------
    checks = job.get("checks") or []
    if checks:
        helpers = _make_helpers(pd, np)
        for chk in checks:
            entry = {"name": chk["name"], "passed": False, "message": "", "weight": chk.get("weight", 1)}
            if not payload["ok"]:
                entry["message"] = "Not evaluated because your code raised an error (see the error above)."
            elif payload["ref_error"]:
                entry["message"] = "Not evaluated: the reference solution failed (content bug)."
            else:
                env = {"user": user_ns, "ref": ref_ns or {}, "figs": figs, "pd": pd, "np": np, "plt": plt, **helpers}
                env["need"] = helpers["make_need"](user_ns)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        exec(compile(chk["code"], f"<check {chk['name']}>", "exec"), env)
                    entry["passed"] = True
                except AssertionError as exc:
                    entry["message"] = str(exc) or chk.get("hint", "Check failed.")
                except Exception as exc:
                    entry["message"] = f"{type(exc).__name__}: {exc}"
            payload["checks"].append(entry)

    real_stdout.write("\n" + nonce + json.dumps(payload, default=_jsonable) + "\n")
    real_stdout.flush()


def _make_helpers(pd, np):
    def close(a, b, tol=1e-6, rel=1e-6):
        try:
            return abs(float(a) - float(b)) <= max(tol, rel * abs(float(b)))
        except (TypeError, ValueError):
            return False

    def make_need(ns):
        def need(name, kind=None):
            if name not in ns:
                raise AssertionError(f"Variable `{name}` was not defined. The task asks you to store your answer in `{name}`.")
            val = ns[name]
            if kind is not None and not isinstance(val, kind):
                names = kind.__name__ if isinstance(kind, type) else " or ".join(k.__name__ for k in kind)
                raise AssertionError(f"`{name}` should be a {names}, but it is a {type(val).__name__}.")
            return val
        return need

    def frames_match(user_df, ref_df, sort_by=None, check_order=False, rtol=1e-4, atol=1e-6, columns=None, ignore_index=True):
        """Compare two frames column-by-column with tolerant numeric matching."""
        if isinstance(user_df, pd.Series):
            user_df = user_df.to_frame()
        if isinstance(ref_df, pd.Series):
            ref_df = ref_df.to_frame()
        if not isinstance(user_df, pd.DataFrame):
            raise AssertionError(f"Expected a DataFrame but got {type(user_df).__name__}.")
        u, r = user_df.copy(), ref_df.copy()
        if ignore_index:
            if not isinstance(u.index, pd.RangeIndex):
                u = u.reset_index()
            if not isinstance(r.index, pd.RangeIndex):
                r = r.reset_index()
        u.columns = [str(c).lower() for c in u.columns]
        r.columns = [str(c).lower() for c in r.columns]
        cols = [c.lower() for c in (columns or r.columns)]
        missing = [c for c in cols if c not in u.columns]
        if missing:
            raise AssertionError(f"Missing column(s): {missing}. Your columns: {list(u.columns)}.")
        u, r = u[cols], r[cols]
        if len(u) != len(r):
            raise AssertionError(f"Expected {len(r)} rows but your result has {len(u)}. Check your filters and grouping.")
        if not check_order:
            keys = [c.lower() for c in (sort_by or cols)]
            u = u.sort_values(keys, kind="mergesort").reset_index(drop=True)
            r = r.sort_values(keys, kind="mergesort").reset_index(drop=True)
        else:
            u, r = u.reset_index(drop=True), r.reset_index(drop=True)
        for c in cols:
            a, b = u[c], r[c]
            if pd.api.types.is_numeric_dtype(b) and not pd.api.types.is_bool_dtype(b):
                a_num = pd.to_numeric(a, errors="coerce")
                if not np.allclose(a_num.astype(float), b.astype(float), rtol=rtol, atol=atol, equal_nan=True):
                    bad = int((~np.isclose(a_num.astype(float), b.astype(float), rtol=rtol, atol=atol, equal_nan=True)).argmax())
                    raise AssertionError(f"Values in column '{c}' differ, e.g. row {bad}: expected {b.iloc[bad]!r}, got {a.iloc[bad]!r}.")
            else:
                if not (a.astype(str).values == b.astype(str).values).all():
                    bad = int((a.astype(str).values != b.astype(str).values).argmax())
                    raise AssertionError(f"Values in column '{c}' differ, e.g. row {bad}: expected {b.iloc[bad]!r}, got {a.iloc[bad]!r}.")
        return True

    return {"close": close, "frames_match": frames_match, "make_need": make_need}


if __name__ == "__main__":
    main()
