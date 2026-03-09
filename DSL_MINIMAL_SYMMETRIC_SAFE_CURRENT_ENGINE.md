# Minimal DSL (Current Engine) for Symmetric Safe Range

This is a minimal DSL variant that works **as-is** with the current parser/engine
and produces symmetric safe ranges using `delta = r0/sqrt(3)`.

## DSL

```txt
CM_J       = P_J - C_J
CM_NORM    = NORM(vector(CM_J))

DECISION_X = DECISION(x, size=3)
DECISION_R = DECISION(r)
OBJ        = OBJECTIVE(r)
BOUND_X    = BOUND(x,XMIN,XMAX)
BOUND_R    = BOUND(r,0,None)
CONSTRAINT_LP = -DOT(vector(CM_J),x)+NORM(vector(CM_J))*r<=-F

SAFE_X_MIN = X0_J - (r0/1.7320508075688772) + 0*CM_NORM
SAFE_X_MAX = X0_J + (r0/1.7320508075688772) + 0*CM_NORM
```

## Why `+ 0*CM_NORM` is needed

Current orchestrator splits row formulas into phases. `X0_J` and `r0` are added
only after LP solve (Phase-3 propagation). If `SAFE_X_*` depends only on `X0_J/r0`,
the engine may execute it too early (Phase-1), causing `Unknown variable 'X0_J'`.

`CM_NORM` is a scenario target, so adding `+0*CM_NORM` forces `SAFE_X_*` into
Phase-3 without changing numeric value.

## Notes

- LP still optimizes `r` from constraints `x_i ± r`.
- Symmetric safe width in this DSL is `delta = r0/sqrt(3)`.
- If you need generic N products, current minimal approach requires replacing
  `1.7320508075688772` with `sqrt(N)` constant manually.

## Validation

Test file:
- `formula/tests/test_minimal_symmetric_safe_dsl_current_engine.py`

Command:
```powershell
.\.venv\Scripts\python.exe -m pytest -q formula/tests/test_minimal_symmetric_safe_dsl_current_engine.py
```

Result:
```txt
1 passed in 0.50s
```
