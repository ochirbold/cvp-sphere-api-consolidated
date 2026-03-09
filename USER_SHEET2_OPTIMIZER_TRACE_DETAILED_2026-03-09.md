# Sheet2 Optimizer LP Trace Report (Detailed)

Date: 2026-03-09
Workspace: `D:\VS CODE\sphere-problem\cvp-sphere-api-consolidated`

## 1) Өгөгдөл

- `p1 = 15`, `c1 = 7`
- `p2 = 17`, `c2 = 11`
- `F = 2700`
- `xmin1 = 0`, `xmax1 = 3800`
- `xmin2 = 0`, `xmax2 = 7800`
- Start (reference only): `x1=1`, `x2=1`, `r=1`

Derived:
- `cm1 = p1-c1 = 8`
- `cm2 = p2-c2 = 6`
- `cm_norm = sqrt(cm1^2 + cm2^2) = sqrt(64+36)=10`

## 2) Энэ тестэд optimizer-д өгсөн DSL

Тестийн зорилго нь таны хүссэн жишээний шийд (`x1=x2=r=1900`) болон projected safe range-уудыг гаргах тул дараах DSL-ийг ажиллуулсан:

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
XMIN = [0, 0]
XMAX = [3800, 7800]
```

Тайлбар:
- `C_FIX_X1`, `C_FIX_X2` нь `x1<=r`, `x2<=r` холбоос өгнө.
- MatrixBuilder автоматаар coupled bounds нэмдэг:
  - `-xj + r <= -xmin_j`
  - `xj + r <= xmax_j`
- `xmin=0` үед `-xj+r<=0` нь `r<=xj` утгатай. Иймээс дээрхтэй нийлээд `xj=r` тогтоно.

## 3) LP parser-ийн гаргасан spec

Script-run output:

```txt
variables(spec)= ['r', 'x', 'x1', 'x2']
constraints(spec)= ['BOUND_R', 'CONSTRAINT_LP', 'C_FIX_X1', 'C_FIX_X2']
bounds(spec)= ['__dsl_bound_r']
```

Дараа нь deterministic builder base `x`-ийг шүүж variable order-ийг:

```txt
['x1', 'x2', 'r']
```

болгож тогтоосон.

## 4) Үүссэн LP матриц

Objective vector (`c`):

```txt
c = [8.0, 6.0, -10.0]
```

Constraint matrix (`A_ub`) ба RHS (`b_ub`):

```txt
Row0: [-8, -6, 10]   <= -2700     (main)
Row1: [ 1,  0,-1]    <= 0         (x1-r<=0)
Row2: [ 0,  1,-1]    <= 0         (x2-r<=0)
Row3: [-1,  0, 1]    <= 0         (auto: -x1+r<=-xmin1, xmin1=0)
Row4: [ 1,  0, 1]    <= 3800      (auto:  x1+r<=xmax1)
Row5: [ 0, -1, 1]    <= 0         (auto: -x2+r<=-xmin2, xmin2=0)
Row6: [ 0,  1, 1]    <= 7800      (auto:  x2+r<=xmax2)
```

Full vectors:

```txt
A_ub = [
  [-8.0, -6.0, 10.0],
  [ 1.0,  0.0,-1.0],
  [ 0.0,  1.0,-1.0],
  [-1.0,  0.0, 1.0],
  [ 1.0,  0.0, 1.0],
  [ 0.0, -1.0, 1.0],
  [ 0.0,  1.0, 1.0]
]

b_ub = [-2700.0, 0.0, 0.0, 0.0, 3800.0, 0.0, 7800.0]
```

Bounds:

```txt
x1: (0, None)
x2: (0, None)
r : (0, None)
```

## 5) Solver LP-г хэрхэн ажиллуулсан

`LPSolver.solve(..., maximize=True)` үед:
- SciPy `linprog` нь minimization хийдэг тул solver `c`-г дотроо `-c` болгоод ажиллуулна.
- Тиймээс дотоод solve нь `min(-8*x1 -6*x2 +10*r)` хэлбэрт орно.
- Энэ нь анхны `max(8*x1 + 6*x2 -10*r)`-тэй эквивалент.

HiGHS-ийн гаргасан хариу:

```txt
success = True
x = [1900.0, 1900.0, 1900.0]
fun = 7600.0
message = Optimization terminated successfully. (HiGHS Status 7: Optimal)
```

Variable order нь `['x1','x2','r']` тул:
- `x1 = 1900`
- `x2 = 1900`
- `r = 1900`

`fun` шалгалт:
- `8*1900 + 6*1900 - 10*1900 = 15200 + 11400 - 19000 = 7600`

## 6) `safexmin`, `safexmax` хэрхэн тооцогдсон

`volume_optimizer` дотор projected range нь Sheet2 дүрмээр:
- `alpha_j = p_j / ||p||`
- `||p|| = sqrt(p1^2 + p2^2) = sqrt(15^2+17^2) = sqrt(514) = 22.6715680975`

Тэгвэл:
- `alpha1 = 15 / 22.6715680975 = 0.6616216371`
- `alpha2 = 17 / 22.6715680975 = 0.7498378554`

Projected safe ranges:
- `x1 safexmin = x1 - alpha1*r = 1900 - 0.6616216371*1900 = 642.9188895`
- `x1 safexmax = x1 + alpha1*r = 1900 + 0.6616216371*1900 = 3157.0811105`
- `x2 safexmin = x2 - alpha2*r = 1900 - 0.7498378554*1900 = 475.3080748`
- `x2 safexmax = x2 + alpha2*r = 1900 + 0.7498378554*1900 = 3324.6919252`

Rounded:
- `x1`: `642.9189` ~ `3157.081`
- `x2`: `475.3081` ~ `3324.692`

## 7) Тестийн баталгаажуулалт

Run command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q formula/tests/test_user_requested_sheet2_example.py
```

Result:

```txt
.                                                                        [100%]
1 passed in 0.67s
```

## 8) Холбогдох файлууд

- Test: `formula/tests/test_user_requested_sheet2_example.py`
- Service: `formula/core/volume_optimizer.py`
- Parser: `formula/lp/parser.py`
- Matrix builder: `formula/lp_matrix_builder_deterministic_complete.py`
- Solver: `formula/lp_solver.py`
