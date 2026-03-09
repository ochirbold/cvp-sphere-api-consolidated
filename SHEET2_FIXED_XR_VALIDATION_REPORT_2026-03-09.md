# Fixed-Point Validation Report: Sheet2 Excel vs Optimizer Projection

- Date: 2026-03-09
- Workspace: `cvp-sphere-api-consolidated`
- Test file: `formula/tests/test_sheet2_fixed_xr_projection.py`
- Command run:
  - `C:\edb\languagepack\v4\Python-3.11\python.exe -m pytest formula/tests/test_sheet2_fixed_xr_projection.py -q -s`
- Result: `1 passed`

## Goal

Validate that, for the exact Excel Sheet2 fixed point:
- `x1 = 1900`
- `x2 = 1900`
- `r = 1900`

our optimizer projection output (`projectedRange`) matches Excel formula outputs:
- `xmin = x - (p/||p||)*r`
- `xmax = x + (p/||p||)*r`

## Inputs

- Product 1: `p1=15`, `c1=7`, `xmin=0`, `xmax=3800`
- Product 2: `p2=17`, `c2=11`, `xmin=0`, `xmax=7800`
- Fixed cost: `F=2700`

## Test Method (How we forced exact Excel point)

Because optimizer normally finds its own optimum, the test **patches solver output** to:
- `x = [x1, x2, r] = [1900, 1900, 1900]`

Then the production response code computes `projectedRange` exactly as optimizer would in real run.

This validates output computation logic without changing production code path.

## Step-by-step Calculation

1. Compute norm:
- `||p|| = sqrt(15^2 + 17^2) = sqrt(514) = 22.6715680975`

2. Compute factors:
- `alpha1 = 15/||p|| = 0.6616216371`
- `alpha2 = 17/||p|| = 0.7498378554`

3. Projected ranges with `x=1900`, `r=1900`:

Product 1:
- `xmin1 = 1900 - 1900*0.6616216371 = 642.9188895`
- `xmax1 = 1900 + 1900*0.6616216371 = 3157.0811105`

Product 2:
- `xmin2 = 1900 - 1900*0.7498378554 = 475.3080748`
- `xmax2 = 1900 + 1900*0.7498378554 = 3324.6919252`

## Compared Against Expected Excel Values

Expected:
- `xmin: 642.9189, 475.3081`
- `xmax: 3157.081, 3324.692`

Optimizer test output (rounded):
- Product 1: `xmin=642.9189`, `xmax=3157.081`
- Product 2: `xmin=475.3081`, `xmax=3324.692`

Status:
- All assertions PASS (exact `isclose` + rounded value checks).

## Conclusion

`cvp-sphere-api-consolidated` optimizer projection logic reproduces Excel Sheet2 fixed-point results for `x1=x2=1900, r=1900` exactly as expected.
