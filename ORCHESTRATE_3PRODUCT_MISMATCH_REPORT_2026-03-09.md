# 3-Product Orchestrate Test Report (Mismatch Analysis)

Date: 2026-03-09

## 1) Input Parameters

Given case:
- `p1=700`, `c1=280` -> `cm1=420`
- `p2=1120`, `c2=420` -> `cm2=700`
- `p3=4480`, `c3=2240` -> `cm3=2240`
- `F=14000`
- Bounds:
  - `x1 in [6.66, 26.66]`
  - `x2 in [4, 16]`
  - `x3 in [1.25, 5]`

CM norm:
- `CM_NORM = sqrt(420^2 + 700^2 + 2240^2) = 2384.114091229696`

## 2) Orchestrator DSL Used in Test

```txt
CM_J       = P_J - C_J
CM_NORM    = NORM(vector(CM_J))
SAFE_X_MIN = X0_J - r0*(CM_J/CM_NORM)
SAFE_X_MAX = X0_J + r0*(CM_J/CM_NORM)
DECISION_X = DECISION(x, size=3)
DECISION_R = DECISION(r)
OBJ        = OBJECTIVE(r)
BOUND_X    = BOUND(x,XMIN,XMAX)
BOUND_R    = BOUND(r,0,None)
CONSTRAINT_LP = -DOT(vector(CM_J),x)+NORM(vector(CM_J))*r<=-F
```

## 3) LP Model Built by Orchestrator

Decision variables: `x1, x2, x3, r`

Objective:
- `max r`

Constraints:
- `420*x1 + 700*x2 + 2240*x3 - 2384.1141*r >= 14000`
- `x1-r >= 6.66`, `x1+r <= 26.66`
- `x2-r >= 4`, `x2+r <= 16`
- `x3-r >= 1.25`, `x3+r <= 5`
- `r >= 0`

Equivalent width limits from bounds:
- `r <= (26.66-6.66)/2 = 10`
- `r <= (16-4)/2 = 6`
- `r <= (5-1.25)/2 = 1.875`

Therefore global optimum radius is constrained by item 3:
- `r* = 1.875`

## 4) Actual Orchestrate Result (Executed)

From test run:
- `x1 = 24.785`
- `x2 = 14.125`
- `x3 = 3.125`
- `r = 1.875`

Phase-3 safe values (current DSL formula):
- Row1 (`CM_J=420`): `SAFE_X_MIN=24.4547`, `SAFE_X_MAX=25.1153`
- Row2 (`CM_J=700`): `SAFE_X_MIN=13.5745`, `SAFE_X_MAX=14.6755`
- Row3 (`CM_J=2240`): `SAFE_X_MIN=1.3633`, `SAFE_X_MAX=4.8867`

## 5) Target You Provided

Target:
- `x1=8.54`, `x2=11.26`, `x3=3.12`
- `r=1.0825`
- safe ranges:
  - `x1: [7.46, 9.62]`
  - `x2: [10.18, 12.34]`
  - `x3: [2.04, 4.21]`

## 6) Why Results Differ

There are 3 distinct reasons:

1. Radius definition mismatch (`r` vs `delta`)
- In current LP, optimized variable is `r` in constraints `x_i ± r`.
- So solver's radius is `r*=1.875`.
- Your target `1.0825` is actually:
  - `delta = r*/sqrt(3) = 1.875/sqrt(3) = 1.08253`
- So your text labels `delta` as `r`.

2. Safe-range formula mismatch
- Current DSL uses directional formula:
  - `SAFE_X_MIN = X0_J - r0*(CM_J/CM_NORM)`
  - `SAFE_X_MAX = X0_J + r0*(CM_J/CM_NORM)`
- Your target ranges are symmetric with constant half-width `delta=1.0825` for all items.
- These are different definitions, therefore outputs differ by design.

3. Multiple optimal centers when objective is only `max r`
- Once `r=1.875` is fixed by tightest bound (item 3), several `(x1,x2)` pairs can remain feasible.
- LP has no secondary objective to force the specific center `(8.54, 11.26, 3.12)`.
- Current solver selected one valid optimum near upper bounds for x1/x2.

## 7) Correct Safe-Range Formula for Your Target Table

If you want exactly your documented ranges, use:
- `delta = r0 / sqrt(3)`
- `SAFE_X_MIN = X0_J - delta`
- `SAFE_X_MAX = X0_J + delta`

With `r0=1.875`:
- `delta = 1.08253`

Then with centers `(8.54, 11.26, 3.12)`:
- `x1: 8.54 ± 1.0825 -> [7.46, 9.62]`
- `x2: 11.26 ± 1.0825 -> [10.18, 12.34]`
- `x3: 3.12 ± 1.0825 -> [2.04, 4.21]`

## 8) Executed Test Artifact

Test file:
- `formula/tests/test_three_product_orchestrate_mismatch_analysis.py`

Command:
```powershell
.\.venv\Scripts\python.exe -m pytest -q formula/tests/test_three_product_orchestrate_mismatch_analysis.py
```

Result:
```txt
1 passed in 0.50s
```
