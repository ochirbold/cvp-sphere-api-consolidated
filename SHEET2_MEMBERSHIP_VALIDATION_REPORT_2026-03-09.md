# Sheet2 Solver Membership Validation Report

- Date: 2026-03-09
- Project: `cvp-sphere-api-consolidated`
- Test file: `formula/tests/test_sheet2_membership_detailed.py`
- Command:
  - `C:\edb\languagepack\v4\Python-3.11\python.exe -m pytest formula/tests/test_sheet2_membership_detailed.py -q -s`
- Result: `1 passed`

## 1) Input Values (Sheet2 exact model)

- Price/Cost:
  - `p1 = 15`, `c1 = 7` => `cm1 = 8`
  - `p2 = 17`, `c2 = 11` => `cm2 = 6`
- Fixed cost: `F = 2700`
- Constraint bounds:
  - `x1` projected range must be inside `[xmin1, xmax1] = [0, 3800]`
  - `x2` projected range must be inside `[xmin2, xmax2] = [0, 7800]`

Derived coefficients:
- `||CM|| = sqrt(8^2 + 6^2) = 10`
- `alpha = p1 / sqrt(p1^2 + p2^2) = 15/sqrt(514) = 0.6616216370868463`
- `beta  = p2 / sqrt(p1^2 + p2^2) = 17/sqrt(514) = 0.7498378553650925`

## 2) LP Built From DSL (Step-by-step)

Decision variables:
- `x1, x2, r`

Objective (maximize):
- `Z = 8*x1 + 6*x2 - 10*r`

Constraint rows generated:
1. `-8*x1 - 6*x2 + 10*r <= -2700`
2. `-x1 + 0.6616216371*r <= 0`
3. ` x1 + 0.6616216371*r <= 3800`
4. `-x2 + 0.7498378554*r <= 0`
5. ` x2 + 0.7498378554*r <= 7800`
6. `r >= 0` (bound)

## 3) Solver Output

Optimal solution:
- `x1 = 3800`
- `x2 = 7800`
- `r = 0`

Objective value:
- LP part: `8*3800 + 6*7800 - 10*0 = 77100`
- Excel objective with fixed cost: `77100 - 2700 = 74400`

## 4) Membership Check You Asked About

Projected ranges:
- `x1_min_proj = x1 - alpha*r = 3800 - 0.6616216371*0 = 3800`
- `x1_max_proj = x1 + alpha*r = 3800 + 0.6616216371*0 = 3800`
- `x2_min_proj = x2 - beta*r  = 7800 - 0.7498378554*0 = 7800`
- `x2_max_proj = x2 + beta*r  = 7800 + 0.7498378554*0 = 7800`

Constraint interval membership:
- `x1_min_proj = 3800` is in `[0, 3800]` -> PASS
- `x1_max_proj = 3800` is in `[0, 3800]` -> PASS
- `x2_min_proj = 7800` is in `[0, 7800]` -> PASS
- `x2_max_proj = 7800` is in `[0, 7800]` -> PASS

Main profitability constraint check:
- LHS = `-8*3800 - 6*7800 + 10*0 = -77100`
- RHS = `-2700`
- `-77100 <= -2700` -> PASS

## 5) Conclusion

Таны асуултад шууд хариулбал:
- **Тийм.** Энэ Sheet2 exact загварт манай CVP төслийн бодолтын гаргасан projected `xmin/xmax` утгууд constraint-ийн өгөгдсөн муж дотор бүрэн багтаж байна.
- Мөн solution нь Sheet2 fixture-ийн хүлээгдэж буй үр дүнтэй (`x1=3800, x2=7800, r=0`) таарч байна.
