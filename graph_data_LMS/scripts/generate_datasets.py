"""(Re)generate every practice dataset from seeded generators.

Usage:  python scripts/generate_datasets.py [--force]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics_lab.config import get_paths  # noqa: E402
from analytics_lab.data.generate import build_all  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="regenerate even if the current version exists")
    args = ap.parse_args()
    path = build_all(force=args.force)
    print(f"Warehouse: {path}")
    print(json.dumps(json.loads(get_paths().manifest.read_text()), indent=2))
