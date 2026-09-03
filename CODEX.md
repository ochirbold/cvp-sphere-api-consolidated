# CVP Sphere API Codex Rules

This file is the project constitution for Codex work in this repository. Treat it as the local equivalent of a `CLAUDE.md`: it defines the main line of the system, what is production-relevant, what is stale, and how to change the project without breaking deployed behavior.

## Noён Шугам

`cvp-sphere-api-consolidated` is a FastAPI service for CVP optimization and an Oracle-backed, indicator-driven formula engine.

The production formula path is:

1. API request enters `main.py`.
2. `indicator_id` is used to read `kpi_indicator.TABLE_NAME`.
3. Formulas are read from `kpi_indicator_indicator_map` by `main_indicator_id`.
4. `formula/pythoncode.py` is used only as a compatibility shim.
5. Real execution lives in `formula/core/orchestrator.py`.
6. The selected Oracle table is queried, formulas are classified/executed, LP formulas use the deterministic LP pipeline, and computed values are written back to the same table.

Do not replace this path with a new execution path unless the user explicitly asks for a migration.

## Canonical API

`POST /formula/calculate` is the canonical formula endpoint.

Supported formula mode:

- `mode = "indicator_current"`
- omitted `mode`, which keeps the same legacy behavior and runs the current indicator execution path

`POST /formula/optimize` is only a compatibility alias. It must forward to `indicator_current`; it is not a new optimizer-only API.

`POST /formula/calculate/direct` is not the production formula path unless the repo has been intentionally migrated and tests/docs prove that migration.

## Scenario Filtering

`scenario_code` is an optional request-level filter for formula execution.

Rules:

- `scenario_code = null`, missing, or empty after trimming means all rows are included.
- A non-empty `scenario_code` means only rows with matching `SCENARIO_CODE` are selected and updated.
- If `scenario_code` is requested but the selected table has no `SCENARIO_CODE` column, fail clearly instead of silently ignoring the filter.
- Keep backward-compatible request aliases where already supported, including `scenario_Code` and `scenarioCode`.
- No database schema change or new environment variable is required for normal API callers.

Important: live formula runs update Oracle data. Only run them against real DB tables when the user has explicitly authorized the indicator and scenario scope.

## Files That Matter

Treat these as production-relevant unless new evidence says otherwise:

- `main.py`
- `formula/pythoncode.py`
- `formula/core/orchestrator.py`
- `formula/core/runtime.py`
- `formula/lp/*`
- `formula/lp_matrix_builder_deterministic_complete.py`
- `formula/lp_solver.py`
- `formula/tests/test_lp_regression.py`
- `formula/tests/test_scenario_code_filter.py`
- `scripts/check_no_duplicates.py`
- `scripts/import_smoke.py`
- `requirements.txt`
- `Dockerfile`, only if the custom host runs the app by container

Use existing helper functions and runtime boundaries before adding new abstractions.

## Stale Or Non-Authoritative Material

These areas are useful context, not source of truth:

- `railway.json`: historical unless the user confirms Railway is active again.
- `DEPLOYMENT_PACKAGE_README.md`: stale deployment guidance; it references old repo/branch assumptions and must not be followed blindly.
- `docs/archive/**`: research and historical notes, not production instructions.
- `formulaQE/**`: experiments or historical material unless the user explicitly asks to revive it.
- `.venv*`, `.codex_pydeps`, `__pycache__/*.pyc`, and backup patch files: local/generated pollution. Do not stage or modify them as part of normal work.

If deployment facts are needed, inspect GitHub remote/branch state and ask the user about the custom host rather than trusting old Railway-oriented docs.

## Git And Deployment Rules

Current source of truth is the GitHub remote named `origin`. The deployed host is custom, not Railway, unless the user says otherwise.

Default branch observed for this repo is `master`. Do not assume `main`.

Before pushing:

- Run `git status --short --branch`.
- Stage only intentional files. Do not use `git commit -a`.
- Do not commit `.env`, credentials, virtual environments, `__pycache__`, `.pyc`, generated backups, or local verification folders.
- Prefer a feature branch and PR for behavior changes.
- If the custom host deploys from `master`, the host admin usually needs to pull the merged `master` commit and restart the service according to their supervisor/process manager.

No GitHub Actions deploy workflow is currently authoritative unless one is added later. Existing CI guards are checks, not proof of deployment.

## Verification

For formula-engine changes, run the closest available CI-equivalent checks:

```bash
python - <<'PY'
import ast
from pathlib import Path
for path in ["main.py", "formula/core/orchestrator.py"]:
    ast.parse(Path(path).read_text(encoding="utf-8"), filename=path)
print("syntax ok")
PY
python scripts/check_no_duplicates.py
python scripts/import_smoke.py
pytest formula/tests/test_lp_regression.py formula/tests/test_scenario_code_filter.py -q
git diff --check
```

Use the repo virtual environment when available.

For live API verification, remember:

- `indicator_id` chooses the working table through `kpi_indicator`.
- `scenario_code = null` covers all rows.
- `scenario_code = "base"` covers only `SCENARIO_CODE = 'base'` rows.
- A successful live run may already have changed Oracle rows.

## Change Discipline

Preserve backward compatibility by default. New request fields should be optional, and missing-field behavior should stay unchanged.

Use Oracle bind parameters for values. Avoid broad `SELECT *` changes in the formula engine. Preserve table/column quoting behavior and existing identifier sanitation.

When the repo is dirty, assume unrecognized changes belong to the user. Work around them, do not revert them.

Keep cleanup separate from behavior changes. Removing tracked generated files, deleting stale docs, or reorganizing archives should be its own explicit hygiene change, not bundled into runtime fixes.

## Open Cleanup Backlog

These are good future tasks, but do not mix them into unrelated fixes:

- Document the actual custom host service name, deploy path, restart command, and runtime user.
- Replace or retire stale Railway/deployment docs.
- Remove tracked generated artifacts such as `.pyc` and virtual environment files through a dedicated cleanup PR.
- Decide whether `formulaQE/**` should be archived, deleted, or documented as a historical experiment.
- Pin dependency versions if production reproducibility becomes a priority.
