# Deprecated Manifest

Status: Phase F completed (archive-based cleanup applied).

## Archived (docs/archive/deprecated)

- main_backup.py
- formula/pythoncode_with_lp.py
- formula/formula_runtime_complete.py
- formula/lp_matrix_builder_complete.py

## Archived (docs/archive/research)

- architecture/roadmap/profit-dominance analysis and planning documents
- implementation_prompt.md
- formula README and one-off SQL notes

## Archived (docs/archive/legacy-tests)

- legacy root-level formula test/validation scripts migrated out of runtime tree

## Temporary Runtime Exception

- formula/lp_matrix_builder_deterministic_complete.py

Reason: current orchestrator fallback path still depends on this during transition.
Planned removal: after orchestrator fully switches to `formula.lp.builder` runtime path and regression passes.
