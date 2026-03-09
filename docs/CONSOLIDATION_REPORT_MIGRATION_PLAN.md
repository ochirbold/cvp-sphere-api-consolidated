# Consolidation Report + Migration Plan

Date: 2026-03-09
Scope: `D:\VS CODE\sphere-problem\cvp-sphere-api`

## 1) Executive Summary

This project contains two parallel implementation timelines with one shared product goal.
Current status is functional but structurally fragmented, with duplicate modules and split entrypoints.

Professional recommendation: perform a controlled consolidation in phases (not a big-bang rewrite), define canonical modules, and keep compatibility shims during transition.

## 2) Current-State Findings

### 2.1 Parallel API Entrypoints

- `main.py`
  - Has: `POST /formula/calculate`, `POST /formula/calculate/direct`
  - Missing: `POST /optimize`
- `main_backup.py`
  - Has: `POST /optimize`
  - Does not represent current primary formula API shape
- `cvp-api-deployment-package/main.py` (outside this folder) includes both optimize + formula flow, creating drift risk across environments.

Impact:
- Documentation and runtime behavior are inconsistent depending on which file is deployed.

### 2.2 LP Module Version Drift

In `formula/`, multiple LP-generation lines coexist:

- Newer line:
  - `matrix_builder_v3.py`
  - `lp_solver_engine.py`
- Older line still used by orchestrator:
  - `lp_matrix_builder_deterministic_complete.py`
  - `lp_solver.py`

`pythoncode.py` currently imports the older line:
- `from lp_matrix_builder_deterministic_complete import LPMatrixBuilder`
- `from lp_solver import LPSolver`

Impact:
- Architecture document says one direction, runtime uses another.
- Refactoring without compatibility strategy can break production flows.

### 2.3 Repository Hygiene

- Research/analysis docs, validation scripts, and production runtime are mixed in same runtime folder.
- `venv` directory exists in repo folder (ignored by parent `.gitignore`, but still operationally noisy).

Impact:
- Slower onboarding, harder code ownership, higher accidental-edit probability.

## 3) Canonicalization Decisions (Target State)

### 3.1 Canonical Runtime Components

Keep as canonical now:

- API:
  - `main.py` (becomes single API entrypoint, merge `/optimize` into it)
- Orchestration:
  - `formula/pythoncode.py`
- Runtime evaluator:
  - `formula/formula_runtime.py`
- DSL/AST:
  - `formula/dsl_parser.py`
  - `formula/constraint_extractor.py`
  - `formula/ast_expression_parser.py`
- Utilities:
  - `formula/unicode_normalizer.py`

LP canonical choice (recommended):
- Prefer `matrix_builder_v3.py` + `lp_solver_engine.py` as target canonical line.
- Keep compatibility wrappers while migrating `pythoncode.py`.

### 3.2 Files to Deprecate

Deprecate first, remove later after validation:

- `main_backup.py`
- `formula/pythoncode_with_lp.py`
- `formula/formula_runtime_complete.py`
- `formula/lp_matrix_builder_complete.py`
- `formula/lp_matrix_builder_deterministic_complete.py`
- `formula/lp_solver.py`

## 4) Recommended Folder Structure Mapping

Target structure (aligned with roadmap) and mapping from current files:

- `formula/core/orchestrator.py` <- `formula/pythoncode.py`
- `formula/core/runtime.py` <- `formula/formula_runtime.py`
- `formula/lp/parser.py` <- `formula/lp_model_parser.py`
- `formula/lp/builder.py` <- `formula/matrix_builder_v3.py`
- `formula/lp/solver.py` <- `formula/lp_solver_engine.py`
- `formula/dsl/parser.py` <- `formula/dsl_parser.py`
- `formula/dsl/extractor.py` <- `formula/constraint_extractor.py`
- `formula/ast/parser.py` <- `formula/ast_expression_parser.py`
- `formula/utils/unicode.py` <- `formula/unicode_normalizer.py`
- `formula/config/.env.example` <- `formula/.env.example`
- `formula/tests/*` <- consolidated from:
  - `formula/tests/*.py`
  - root-level `formula/test_*.py` files that are still relevant

Compatibility period:
- Keep thin wrappers at old paths to import new modules until all imports are updated.

## 5) Migration Plan (Professional + Low-Risk)

### Phase A: Freeze + Baseline (1-2 days)

1. Declare consolidation freeze for duplicate module creation.
2. Record baseline contracts:
   - API endpoint behavior snapshots (`/formula/*`, `/optimize`).
   - Formula pipeline result snapshots for representative scenarios.
3. Add a temporary decision log: `docs/ADR-001-canonical-modules.md`.

Exit criteria:
- Team agrees on canonical files and migration gates.

### Phase B: API Unification (2-3 days)

1. Merge `/optimize` flow into `main.py` from `main_backup.py`.
2. Mark `main_backup.py` deprecated with removal date.
3. Align README endpoint list with actual `main.py`.

Exit criteria:
- Single entrypoint file for production API.
- No endpoint drift between docs and code.

### Phase C: Package Restructure with Shims (3-5 days)

1. Create package directories:
   - `formula/core`, `formula/lp`, `formula/dsl`, `formula/ast`, `formula/utils`, `formula/config`.
2. Move canonical modules to target paths (or copy + switch imports gradually).
3. Add shim files at legacy locations that re-export from new packages.

Exit criteria:
- Old imports still work.
- New structure is usable for all new code.

### Phase D: LP Line Consolidation (3-5 days)

1. Switch orchestrator imports to canonical LP line:
   - from `lp_matrix_builder_deterministic_complete`/`lp_solver`
   - to `formula.lp.builder`/`formula.lp.solver`
2. Execute regression scenarios for:
   - feasible LP
   - infeasible LP
   - unbounded LP
3. Remove deprecated LP files after passing regression window.

Exit criteria:
- One LP implementation line only.

### Phase E: Test and CI Hardening (2-4 days)

1. Normalize tests into `formula/tests/`.
2. Add CI checks:
   - import smoke test
   - endpoint smoke test
   - duplicate-file guard (reject known deprecated filenames)
3. Set minimum coverage gate for core modules.

Exit criteria:
- Consolidation protected by CI, not just team discipline.

### Phase F: Cleanup + Archive (1-2 days)

1. Move research/debug files to `docs/archive/` or separate `research/`.
2. Remove deprecated runtime files after release cut.
3. Publish final migration note with before/after file map.

Exit criteria:
- Runtime tree contains only production-required modules.

## 6) Parallel-Development Governance (For Your Exact Situation)

To manage "same goal, two timelines" professionally:

1. Canonical ownership:
   - assign a single owner per domain (`api`, `orchestrator`, `lp`, `dsl`).
2. ADR-first rule:
   - any structural change requires short ADR.
3. No-new-duplicates policy:
   - block `*_backup.py`, `*_complete.py`, second entrypoints in PR checks.
4. Compatibility window:
   - keep shims one release cycle, then remove.
5. Weekly consolidation checkpoint:
   - review drift, decide deprecations, enforce cleanup.

## 7) Risk Register and Mitigation

- Risk: Breaking import paths during refactor
  Mitigation: legacy shims + import smoke tests.

- Risk: API behavior regression
  Mitigation: contract snapshots + endpoint regression tests.

- Risk: LP result drift due to solver/builder switch
  Mitigation: fixed scenario benchmark set with tolerance thresholds.

- Risk: Team continues parallel file creation
  Mitigation: CI guard + branch policy + ADR enforcement.

## 8) Immediate Next Actions (This Week)

1. Approve canonical list in Section 3.
2. Implement Phase B (single API entrypoint).
3. Create target folders and shims (Phase C start).
4. Prepare LP benchmark scenarios for Phase D.
5. Add CI duplicate-file guard.

---

If executed in sequence, this plan provides the fastest safe path to the roadmap folder structure while preserving current runtime stability.
