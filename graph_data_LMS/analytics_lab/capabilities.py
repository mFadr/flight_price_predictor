"""Detect installed dependencies and optional runtimes at startup."""

from __future__ import annotations

import glob
import importlib
import importlib.metadata as md
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass

REQUIRED = [
    ("streamlit", "streamlit", "Application framework"),
    ("pandas", "pandas", "Data manipulation"),
    ("numpy", "numpy", "Numerical computing"),
    ("duckdb", "duckdb", "SQL engine"),
    ("scipy", "scipy", "Statistics and optimisation"),
    ("statsmodels", "statsmodels", "Statistical models"),
    ("sklearn", "scikit-learn", "Machine learning"),
    ("matplotlib", "matplotlib", "Static visualisation"),
    ("plotly", "plotly", "Interactive charts"),
    ("openpyxl", "openpyxl", "Excel files"),
]
OPTIONAL = [
    ("pytest", "pytest", "Automated tests"),
    ("pulp", "PuLP", "Optional mixed-integer optimisation (not required)"),
]

R_INSTALL_HELP = """**R is optional.** All Python, SQL and tool-workshop activities work without it.

To enable the R exercises:

1. Install R from <https://cran.r-project.org/> (Windows: *Download R for Windows -> base*; macOS: the `.pkg`; Linux: `sudo apt install r-base`).
2. Make sure `Rscript` is on your `PATH`, **or** paste the full path to `Rscript` in *Settings* (Windows example: `C:\\Program Files\\R\\R-4.4.1\\bin\\Rscript.exe`).
3. Optional packages used in lesson examples: in R run `install.packages(c("dplyr", "ggplot2"))`. Graded R exercises use base R only.
4. Click **Re-check capabilities** in Settings.
"""


@dataclass
class PackageStatus:
    module: str
    dist: str
    purpose: str
    installed: bool
    version: str | None
    required: bool


@dataclass
class RStatus:
    available: bool
    path: str | None
    version: str | None
    packages: dict[str, bool]


def check_packages() -> list[PackageStatus]:
    out = []
    for group, required in ((REQUIRED, True), (OPTIONAL, False)):
        for module, dist, purpose in group:
            try:
                importlib.import_module(module) if module not in ("streamlit",) else None
                version = md.version(dist)
                ok = True
            except Exception:
                ok, version = False, None
            out.append(PackageStatus(module, dist, purpose, ok, version, required))
    return out


def find_rscript(explicit: str | None = None) -> str | None:
    if explicit and os.path.isfile(explicit):
        return explicit
    exe = shutil.which("Rscript")
    if exe:
        return exe
    if os.name == "nt":
        candidates = sorted(glob.glob(r"C:\Program Files\R\R-*\bin\Rscript.exe"), reverse=True)
        candidates += sorted(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Programs\R\R-*\bin\Rscript.exe")), reverse=True)
    else:
        candidates = ["/usr/bin/Rscript", "/usr/local/bin/Rscript", "/opt/homebrew/bin/Rscript", "/Library/Frameworks/R.framework/Resources/bin/Rscript"]
    return next((c for c in candidates if os.path.isfile(c)), None)


def check_r(explicit: str | None = None) -> RStatus:
    path = find_rscript(explicit)
    if not path:
        return RStatus(False, None, None, {})
    try:
        r = subprocess.run(
            [path, "--vanilla", "-e", 'cat(R.version.string, "\\n"); for (p in c("dplyr","ggplot2")) cat(p, requireNamespace(p, quietly=TRUE), "\\n")'],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return RStatus(False, path, None, {})
    if r.returncode != 0:
        return RStatus(False, path, None, {})
    lines = r.stdout.strip().splitlines()
    version = lines[0].strip() if lines else None
    pkgs = {}
    for ln in lines[1:]:
        parts = ln.split()
        if len(parts) == 2:
            pkgs[parts[0]] = parts[1] == "TRUE"
    return RStatus(True, path, version, pkgs)


def python_info() -> str:
    return f"Python {sys.version.split()[0]} ({sys.executable})"
