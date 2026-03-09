import sys
from pathlib import Path

# Banned patterns
BANNED_NAMES = {
    "main_backup.py",
    "pythoncode_with_lp.py",
    "formula_runtime_complete.py",
    "lp_matrix_builder_complete.py",
    "lp_matrix_builder_deterministic_complete.py",
}

BANNED_SUFFIXES = ("_backup.py", "_complete.py")
SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", ".pytest_cache", "archive"}

# Temporary transition allowlist (remove after full runtime switch)
ALLOWED_TRANSITION_PATHS = {
    "formula/lp_matrix_builder_deterministic_complete.py",
}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    violations = []

    for path in repo.rglob("*.py"):
        if should_skip(path):
            continue

        rel = path.relative_to(repo).as_posix()
        name = path.name

        if rel in ALLOWED_TRANSITION_PATHS:
            continue

        if name in BANNED_NAMES:
            violations.append(rel)
            continue

        if name.endswith(BANNED_SUFFIXES):
            violations.append(rel)

    if violations:
        print("[FAIL] Duplicate/deprecated file guard violations:")
        for v in sorted(violations):
            print(f" - {v}")
        return 1

    print("[OK] Duplicate/deprecated file guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
