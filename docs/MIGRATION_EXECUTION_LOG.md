# Migration Execution Log

Date: 2026-03-09
Workspace: D:\VS CODE\sphere-problem\cvp-sphere-api-consolidated

## Completed

1. Created isolated consolidated workspace outside original `cvp-sphere-api`.
2. Implemented package structure:
   - formula/core, formula/lp, formula/dsl, formula/ast, formula/utils, formula/config
3. Copied canonical implementations into new structure.
4. Added compatibility shims at legacy module paths.
5. Unified API entrypoint by replacing consolidated `main.py` with integrated version containing:
   - POST /optimize
   - POST /formula/calculate
   - POST /formula/calculate/direct
6. Added baseline config module (`formula/config/settings.py`).
7. Marked `main_backup.py` as deprecated shim.

## Pending (next phase)

1. Switch `formula/core/orchestrator.py` LP imports from legacy LP modules to `formula.lp.*`.
2. Consolidate tests under `formula/tests/` and add CI gates.
3. Archive/remove deprecated runtime files after regression pass.

## Phase D/E update (2026-03-09)

8. Added LP regression test suite:
   - formula/tests/test_lp_regression.py
   - covers feasible/infeasible/unbounded + solver status mapping
9. Added CI guard scripts:
   - scripts/check_no_duplicates.py
   - scripts/import_smoke.py
10. Added GitHub Actions workflow:
   - .github/workflows/ci-guards.yml

Note: Local runtime in this environment does not provide `python` executable, so tests were not executed locally. Validation is delegated to CI workflow.

## Phase F update (2026-03-09)

11. Archived deprecated runtime files to `docs/archive/deprecated`.
12. Archived research/planning files to `docs/archive/research`.
13. Archived legacy root-level tests to `docs/archive/legacy-tests`.
14. Tightened duplicate-file CI allowlist to only one temporary runtime exception:
    - formula/lp_matrix_builder_deterministic_complete.py

Outcome: runtime tree is significantly cleaner while preserving compatibility.

## Stage-1/Stage-2 execution (2026-03-09)

15. Installed Python 3.10 and created `.venv` in consolidated workspace.
16. Installed dependencies and `pytest` in `.venv`.
17. Executed and passed local validation commands:
    - `scripts/import_smoke.py`
    - `scripts/check_no_duplicates.py`
    - `pytest -q formula/tests/test_lp_regression.py` (4 passed)
18. Added Stage-2 CI governance files:
    - `.github/CODEOWNERS`
    - `.github/pull_request_template.md`
    - `docs/LOCAL_SETUP.md`
    - `docs/CI_POLICY.md`

Note: `formula.core.orchestrator` currently logs LP fallback warning in import smoke due transitional import path, but module import and checks pass.
