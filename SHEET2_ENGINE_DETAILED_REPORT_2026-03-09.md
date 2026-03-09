# Sheet2 Engine Calculation Report (Detailed Walkthrough)

- Date: 2026-03-09
- Workspace: `D:\VS CODE\sphere-problem\cvp-sphere-api-consolidated`
- Engine path used: `LPModelParser -> LPMatrixBuilder -> LPSolver`
- Test file: `formula/tests/test_sheet2_engine_output.py`
- Test command:
  - `C:\edb\languagepack\v4\Python-3.11\python.exe -m pytest formula/tests/test_sheet2_engine_output.py -q -s`
- Test result: `1 passed`

## 1) Input Data (Excel Sheet2 equivalent)

- Product 1:
  - `p1 = 15`
  - `c1 = 7`
  - `xmin1 = 0`
  - `xmax1 = 3800`
- Product 2:
  - `p2 = 17`
  - `c2 = 11`
  - `xmin2 = 0`
  - `xmax2 = 7800`
- Fixed cost:
  - `F = 2700`

Derived values:
- `cm1 = p1 - c1 = 8`
- `cm2 = p2 - c2 = 6`
- `||CM|| = sqrt(cm1^2 + cm2^2) = sqrt(8^2 + 6^2) = 10`
- `alpha = p1 / sqrt(p1^2 + p2^2) = 15/sqrt(514) = 0.6616216370868463`
- `beta  = p2 / sqrt(p1^2 + p2^2) = 17/sqrt(514) = 0.7498378553650925`

## 2) DSL to LP Mapping

Decision variables:
- `x1, x2, r`

Objective (maximize):
- `Z = 8*x1 + 6*x2 - 10*r`

Constraints:
1. `-8*x1 - 6*x2 + 10*r <= -2700`
2. `-x1 + alpha*r <= 0`
3. ` x1 + alpha*r <= 3800`
4. `-x2 + beta*r <= 0`
5. ` x2 + beta*r <= 7800`
6. `r >= 0`

## 3) Engine Built Matrices (captured from test run)

- Variables order: `['x1', 'x2', 'r']`
- `c = [8.0, 6.0, -10.0]`
- `A_ub`:
  1. `[-8.0, -6.0, 10.0]`
  2. `[-1.0,  0.0, 0.6616216370868463]`
  3. `[ 1.0,  0.0, 0.6616216370868463]`
  4. `[ 0.0, -1.0, 0.7498378553650925]`
  5. `[ 0.0,  1.0, 0.7498378553650925]`
- `b_ub = [-2700.0, -0.0, 3800.0, -0.0, 7800.0]`
- bounds:
  - `x1 >= 0`
  - `x2 >= 0`
  - `r >= 0`

## 4) Solver Result

- Status: `success = True`
- Optimal solution:
  - `x1 = 3800.0`
  - `x2 = 7800.0`
  - `r = 0.0`

Objective value:
- LP objective: `8*3800 + 6*7800 - 10*0 = 77100`
- Excel-style objective (subtract fixed cost):
  - `77100 - 2700 = 74400`

## 5) xmin/xmax Values Engine Would Show

For Sheet2 structure, projected ranges are:
- `x1_min = x1 - alpha*r`
- `x1_max = x1 + alpha*r`
- `x2_min = x2 - beta*r`
- `x2_max = x2 + beta*r`

Substitute solved values (`r=0`):
- `x1_min = 3800 - 0.6616216371*0 = 3800`
- `x1_max = 3800 + 0.6616216371*0 = 3800`
- `x2_min = 7800 - 0.7498378554*0 = 7800`
- `x2_max = 7800 + 0.7498378554*0 = 7800`

So displayed projected ranges are:
- Product 1: `xmin = 3800`, `xmax = 3800`
- Product 2: `xmin = 7800`, `xmax = 7800`

## 6) Membership Check Against Constraint Bounds

Constraint bounds:
- Product 1 bound interval: `[0, 3800]`
- Product 2 bound interval: `[0, 7800]`

Checks:
- `3800` in `[0, 3800]` -> PASS (both min and max)
- `7800` in `[0, 7800]` -> PASS (both min and max)

## 7) Final Conclusion

`cvp-sphere-api-consolidated` engine, when run with Sheet2-equivalent data, computes a valid optimal solution and the resulting projected `xmin/xmax` values are inside the original constraint intervals.

For this exact dataset, the engine output is:
- Product 1 projected range: `[3800, 3800]`
- Product 2 projected range: `[7800, 7800]`
- These match the upper bound edge of each constraint interval.
