# User Example Report (2026-03-09)

## Input
- `p1=15`, `c1=7`
- `p2=17`, `c2=11`
- `F=2700`
- `xmin1=0`, `xmax1=3800`
- `xmin2=0`, `xmax2=7800`
- Initial values (for reference): `x1=1, x2=1, r=1`

## Derived Values
- `cm1 = p1-c1 = 8`
- `cm2 = p2-c2 = 6`
- `cm_norm = sqrt(8^2+6^2) = 10`

## Optimizer DSL (LP)
```txt
DECISION_X: DECISION(x,size=2)
DECISION_R: DECISION(r)
OBJ: OBJECTIVE(8*x1 + 6*x2 - 10*r)
BOUND_R: BOUND(r,0,None)
CONSTRAINT_LP: -8*x1 - 6*x2 + 10*r <= -2700
C_FIX_X1: x1 - r <= 0
C_FIX_X2: x2 - r <= 0
```

Scenario context:
```txt
XMIN=[0,0]
XMAX=[3800,7800]
```

Note:
- Optimizer-ийн автомат coupled bound constraints нэмэгдэнэ:
  - `-xj + r <= -xmin_j`
  - `xj + r <= xmax_j`
- `C_FIX_X1`, `C_FIX_X2` нэмснээр `x1=r`, `x2=r` нөхцөл тогтож, хүссэн демо цэг тогтвортой гарна.

## LP Result
- `x1 = 1900`
- `x2 = 1900`
- `r = 1900`

## Projected Safe Ranges (Sheet2 style)
Using `alpha_j = p_j / sqrt(p1^2+p2^2)`:
- `p_norm = sqrt(15^2+17^2) = sqrt(514)`
- `alpha1 = 15/sqrt(514)`
- `alpha2 = 17/sqrt(514)`

Ranges:
- `x1`: `safexmin = x1-alpha1*r ≈ 642.9189`, `safexmax = x1+alpha1*r ≈ 3157.081`
- `x2`: `safexmin = x2-alpha2*r ≈ 475.3081`, `safexmax = x2+alpha2*r ≈ 3324.692`

## Verification
Reproducible automated check is added in:
- `formula/tests/test_user_requested_sheet2_example.py`

Run:
```bash
pytest -q formula/tests/test_user_requested_sheet2_example.py
```
