import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]

# Only repo root should be added; adding formula dir shadows stdlib modules like `ast`.
sys.path.insert(0, str(repo))

modules = [
    "main",
    "formula.core.orchestrator",
    "formula.core.runtime",
    "formula.lp.parser",
    "formula.lp.builder",
    "formula.lp.solver",
    "formula.dsl.parser",
    "formula.dsl.extractor",
    "formula.ast.parser",
    "formula.utils.unicode",
]

failed = []
for m in modules:
    try:
        __import__(m)
        print(f"[OK] import {m}")
    except Exception as e:
        failed.append((m, str(e)))

if failed:
    print("[FAIL] Import smoke check failed:")
    for m, err in failed:
        print(f" - {m}: {err}")
    raise SystemExit(1)

print("[OK] Import smoke check passed")
