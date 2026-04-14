"""Child-process harness for learner SQL (DuckDB).

Executed as a standalone script; must not import ``analytics_lab``.
The warehouse is opened read-only and external file/network access is disabled
and locked, so queries cannot read arbitrary files through DuckDB table functions.
"""

import datetime
import decimal
import json
import math
import sys
import time
import uuid


def _cell(v):
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        return v.isoformat()
    if isinstance(v, datetime.timedelta):
        return str(v)
    if isinstance(v, (bytes, bytearray)):
        return v.hex()
    if isinstance(v, uuid.UUID):
        return str(v)
    return str(v)


def main() -> None:
    job = json.loads(sys.stdin.read())
    nonce = job.pop("nonce")
    import duckdb

    out = {"results": {}, "setup_error": None}
    try:
        con = duckdb.connect(job["db_path"], read_only=True)
        if job.get("uploads_path"):
            con.execute(f"ATTACH '{job['uploads_path']}' AS uploads (READ_ONLY)")
        if job.get("search_path"):
            con.execute(f"SET search_path = '{job['search_path']}'")
        con.execute("SET enable_external_access = false")
        con.execute("SET lock_configuration = true")
    except Exception as exc:
        out["setup_error"] = f"{type(exc).__name__}: {exc}"
        sys.stdout.write("\n" + nonce + json.dumps(out) + "\n")
        return

    cap = int(job.get("max_rows", 50000))
    for stmt in job["statements"]:
        res = {"ok": True, "columns": [], "types": [], "rows": [], "total_rows": 0, "truncated": False, "error": None, "duration": 0.0}
        t0 = time.perf_counter()
        try:
            cur = con.execute(stmt["sql"])
            if cur.description:
                res["columns"] = [d[0] for d in cur.description]
                res["types"] = [str(d[1]) for d in cur.description]
                rows = cur.fetchmany(cap + 1)
                res["truncated"] = len(rows) > cap
                rows = rows[:cap]
                res["rows"] = [[_cell(v) for v in r] for r in rows]
                res["total_rows"] = len(rows)
        except Exception as exc:
            res["ok"] = False
            res["error"] = f"{type(exc).__name__}: {exc}"
        res["duration"] = round(time.perf_counter() - t0, 4)
        out["results"][stmt["id"]] = res
    sys.stdout.write("\n" + nonce + json.dumps(out) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
