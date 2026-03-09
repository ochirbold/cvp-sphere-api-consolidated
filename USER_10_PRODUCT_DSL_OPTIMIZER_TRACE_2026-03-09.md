# 10-Product DSL Optimizer Validation Report

Date: 2026-03-09
Workspace: `D:\VS CODE\sphere-problem\cvp-sphere-api-consolidated`

## 1) DSL correctness check

Input DSL:
```txt
CM_J	P_J - C_J
CM_NORM	NORM(vector(CM_J))
SAFE_X_MIN	X0_J - r0*(CM_J/CM_NORM)
SAFE_X_MAX	X0_J + r0*(CM_J/CM_NORM)
DECISION_X	DECISION(x, size=10)
DECISION_R	DECISION(r)
OBJ	OBJECTIVE(r)
BOUND_X	BOUND(x,XMIN,XMAX)
BOUND_R	BOUND(r,0,None)
CONSTRAINT_LP	-DOT(vector(CM_J),x)+NORM(vector(CM_J))*r&lt;=-F
```

Check summary:
- `DECISION_X`, `DECISION_R`, `OBJ`, `BOUND_R`, `CONSTRAINT_LP` are parsed and used by LP pipeline.
- `CONSTRAINT_LP` uses `&lt;=`; parser/builder decodes HTML entity and solves correctly.
- `BOUND_X: BOUND(x,XMIN,XMAX)` has an engine limitation: parser stores `lower=None, upper=None` for vector tokens (`XMIN/XMAX`) instead of real numeric bounds.
- Effective x-bounds still work because builder auto-adds coupled constraints from `scenario_context['XMIN']` and `scenario_context['XMAX']`.
- `SAFE_X_MIN`, `SAFE_X_MAX` are not part of LP solve path; they require `X0_J`, `r0` values if you want to evaluate them separately.

Recommended fix pattern when DSL must be fully explicit and portable:
```txt
C_X1_MIN	-x1 + r <= -1000.0
C_X1_MAX	x1 + r <= 7000.0
C_X2_MIN	-x2 + r <= -3000.0
C_X2_MAX	x2 + r <= 18000.0
C_X3_MIN	-x3 + r <= -700.0
C_X3_MAX	x3 + r <= 4500.0
C_X4_MIN	-x4 + r <= -500.0
C_X4_MAX	x4 + r <= 4000.0
C_X5_MIN	-x5 + r <= -1500.0
C_X5_MAX	x5 + r <= 9000.0
C_X6_MIN	-x6 + r <= -2000.0
C_X6_MAX	x6 + r <= 11000.0
C_X7_MIN	-x7 + r <= -2000.0
C_X7_MAX	x7 + r <= 12000.0
C_X8_MIN	-x8 + r <= -3000.0
C_X8_MAX	x8 + r <= 20000.0
C_X9_MIN	-x9 + r <= -4000.0
C_X9_MAX	x9 + r <= 25000.0
C_X10_MIN	-x10 + r <= -5000.0
C_X10_MAX	x10 + r <= 30000.0
```

## 2) LP build trace

- `is_lp_problem = True`
- `variables(spec) = ['r', 'x', 'x1', 'x10', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9']`
- `constraints(spec) = ['BOUND_X', 'BOUND_R', 'CONSTRAINT_LP']`
- `variables(matrix order) = ['x1', 'x10', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'r']`
- `c = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]`
- `#constraints = 21`
- `bounds = [(0.0, None), (0.0, None), (0.0, None), (0.0, None), (0.0, None), (0.0, None), (0.0, None), (0.0, None), (0.0, None), (0.0, None), (0.0, None)]`

Main LP row (from `CONSTRAINT_LP`):
```txt
A_ub[0] = [-9000.0, -3800.0, -4800.0, -13000.0, -16000.0, -5000.0, -6200.0, -7000.0, -2700.0, -3500.0, 25989.61330993595]
b_ub[0] = -30000000.0
```

## 3) Solver execution result

- `success = True`
- `status = 0`
- `message = Optimization terminated successfully. (HiGHS Status 7: Optimal)`
- `objective(fun) = 1750.0`
- `r = 1750.0`

Interpretation:
- Objective is `max r`, so optimum is set by the tightest pair `x_i-r>=xmin_i` and `x_i+r<=xmax_i`.
- Tightest width is product `P007`: `(4000-500)/2 = 1750`, therefore `r* = 1750`.

## 4) x, safe range, projected range results

- Classic safe range: `safeMin = x_i - r`, `safeMax = x_i + r`
- Projected range (optimizer style): `projMin = x_i - (p_i/||P||)*r`, `projMax = x_i + (p_i/||P||)*r`

| Product | x_i | r | safeMin | safeMax | projMin | projMax | xmin | xmax |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P010 | 5250.000000 | 1750.000000 | 3500.000000 | 7000.000000 | 4634.806605 | 5865.193395 | 1000 | 7000 |
| P009 | 16250.000000 | 1750.000000 | 14500.000000 | 18000.000000 | 15914.439966 | 16585.560034 | 3000 | 18000 |
| P008 | 2750.000000 | 1750.000000 | 1000.000000 | 4500.000000 | 1855.173244 | 3644.826756 | 700 | 4500 |
| P007 | 2250.000000 | 1750.000000 | 500.000000 | 4000.000000 | 1187.393227 | 3312.606773 | 500 | 4000 |
| P006 | 7250.000000 | 1750.000000 | 5500.000000 | 9000.000000 | 6914.439966 | 7585.560034 | 1500 | 9000 |
| P005 | 9250.000000 | 1750.000000 | 7500.000000 | 11000.000000 | 8830.549958 | 9669.450042 | 2000 | 11000 |
| P004 | 10250.000000 | 1750.000000 | 8500.000000 | 12000.000000 | 9802.586622 | 10697.413378 | 2000 | 12000 |
| P003 | 18250.000000 | 1750.000000 | 16500.000000 | 20000.000000 | 18068.238315 | 18431.761685 | 3000 | 20000 |
| P002 | 23250.000000 | 1750.000000 | 21500.000000 | 25000.000000 | 23012.311643 | 23487.688357 | 4000 | 25000 |
| P001 | 28250.000000 | 1750.000000 | 26500.000000 | 30000.000000 | 27998.329975 | 28501.670025 | 5000 | 30000 |

## 5) Constraint feasibility checks

- `CM_NORM = 25989.613309935950`
- `DOT(CM_J, x) - CM_NORM*r = 554868176.707612`
- `F = 30000000.000000`
- Check: `554868176.707612 >= 30000000.000000` -> `True`

## 6) Automated test

Test file:
- `formula/tests/test_user_10_product_dsl_optimizer.py`

Executed command:
```powershell
.\.venv\Scripts\python.exe -m pytest -q formula/tests/test_user_10_product_dsl_optimizer.py
```

Execution result:
```txt
.                                                                        [100%]
1 passed in 0.77s
```
