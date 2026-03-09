# Profit Dominance v2.1 Integration - Code-Level Analysis

## SECTION 1 — FILE-BY-FILE CODE-LEVEL IMPACT

### 📄 lp_solver.py

#### Existing Methods Impacted:

1. **`__init__` method** - Must add `tolerance` parameter
2. **`solve` method** - Must integrate binding constraint detection
3. **`_format_result` method** - Must include binding constraints in result
4. **New method needed**: `detect_binding_constraints`

#### Where Binding Logic Would Logically Sit:

- **Primary location**: New `detect_binding_constraints` method
- **Integration point**: Within `solve` method, after obtaining solution but before `_format_result`
- **Data flow**: Constraint matrices (A_ub, b_ub) + solution vector (x) → binding indices/names

#### Parameters That Must Flow In:

1. **From builder**: `A_ub`, `b_ub` (inequality constraints)
2. **From builder**: `A_eq`, `b_eq` (equality constraints - future support)
3. **From builder**: `constraint_names` (mapping indices to meaningful names)
4. **From solver config**: `tolerance` (adaptive scaling parameter)

#### Outputs That Must Change:

1. **Result dictionary**: Add `binding_constraints` key
2. **Content**: List of constraint names (if provided) or indices
3. **Format**: `["constraint_1", "constraint_3"]` or `[0, 2]`

#### Pseudo-Diff Snippets:

**OLD: `__init__` method**

```python
def __init__(
    self,
    method: str = 'highs',
    options: Optional[Dict[str, Any]] = None,
    tolerance: float = 1e-8  # <-- NEW PARAMETER
):
```

**NEW (conceptual): `detect_binding_constraints` method**

```python
def detect_binding_constraints(
    self,
    A_ub: Optional[Matrix] = None,
    b_ub: Optional[Vector] = None,
    x: Optional[Vector] = None,
    constraint_names: Optional[List[str]] = None
) -> List[Union[int, str]]:
    """
    Detect binding constraints after solving.

    Args:
        A_ub: Inequality constraint matrix
        b_ub: Inequality constraint vector
        x: Solution vector
        constraint_names: Optional list of constraint names

    Returns:
        List of binding constraint indices or names
    """
    if A_ub is None or b_ub is None or x is None:
        return []

    # Adaptive tolerance calculation
    residuals = A @ x - b
    binding = []

    for i, r in enumerate(residuals):
        tol = self.tolerance * (1 + abs(b[i]))  # Scale-aware
        if abs(r) <= tol:
            binding.append(i)

    # Return names if provided
    if constraint_names:
        return [constraint_names[i] for i in binding]

    return binding
```

**OLD: `solve` method return**

```python
return {
    'success': bool(result.success),
    'x': x_list,
    'fun': objective_value,
    # ... existing fields
}
```

**NEW (conceptual): `solve` method with binding**

```python
# After solving, before formatting
binding = self.detect_binding_constraints(
    A_ub_list, b_ub_list, result.x, constraint_names
)

# In return dict
return {
    'success': bool(result.success),
    'x': x_list,
    'fun': objective_value,
    'binding_constraints': binding,  # <-- NEW FIELD
    # ... existing fields
}
```

---

### 📄 lp_matrix_builder_deterministic_complete.py

#### Where Constraint Names Should Be Preserved:

1. **In `_build_inequality_constraints` method**: Need to track constraint names alongside matrices
2. **In return dictionary**: Add `constraint_names` key parallel to `A_ub`, `b_ub`
3. **Name extraction**: From formula dictionary keys (constraint formula names)

#### Where Simulate-Mode Branching Would Sit:

1. **New parameter**: `dominance_mode` in `build_from_formulas` method
2. **Branch location**: After building base matrices, before returning
3. **Simulation flow**:
   - Build base matrices
   - If SIMULATE mode: create β-adjusted matrices (multiply RHS by 1.5)
   - Solve both and compare

#### What Must NOT Change:

1. **Formulation logic**: Constraint coefficients (A_ub) must remain unchanged
2. **Variable ordering**: Decision variable order must be preserved
3. **Bounds handling**: Existing bound logic must remain intact
4. **Production default**: Default mode must be "ANALYZE" (no formulation changes)

#### Pseudo-Diff Snippets:

**OLD: `build_from_formulas` return**

```python
return {
    'c': c_vector,
    'A_ub': A_ub_matrix,
    'b_ub': b_ub_vector,
    'bounds': bounds_list,
    'variables': self.decision_variables.copy()
}
```

**NEW (conceptual): With constraint names**

```python
# In _build_inequality_constraints
constraint_names = []  # Track names
for constraint_name in constraint_formulas:
    if constraint_name not in formulas:
        continue
    # ... parse constraint
    if A_row is not None and b_value is not None:
        A_ub_rows.append(A_row)
        b_ub_values.append(b_value)
        constraint_names.append(constraint_name)  # <-- TRACK NAME

# In return dict
return {
    'c': c_vector,
    'A_ub': A_ub_matrix,
    'b_ub': b_ub_vector,
    'constraint_names': constraint_names,  # <-- NEW FIELD
    'bounds': bounds_list,
    'variables': self.decision_variables.copy()
}
```

**NEW (conceptual): SIMULATE mode branching**

```python
def build_from_formulas(
    self,
    formulas: Dict[str, str],
    lp_spec: Dict[str, Any],
    dominance_mode: str = "ANALYZE"  # <-- NEW PARAMETER
) -> Dict[str, Any]:
    # ... existing building logic

    base_matrices = {
        'c': c_vector,
        'A_ub': A_ub_matrix,
        'b_ub': b_ub_vector,
        'constraint_names': constraint_names,
        'bounds': bounds_list,
        'variables': self.decision_variables.copy()
    }

    if dominance_mode == "SIMULATE":
        # Create β-adjusted matrices (RHS * 1.5)
        beta_b_ub = [b * 1.5 for b in b_ub_vector]
        beta_matrices = {
            **base_matrices,
            'b_ub': beta_b_ub
        }
        return {
            'base': base_matrices,
            'beta': beta_matrices,
            'mode': 'SIMULATE'
        }

    return base_matrices
```

---

### 📄 lp_model_parser.py

#### Where Diagnostic Score Belongs:

1. **In `detect_lp_formulas` method**: Add score calculation to returned `lp_spec`
2. **New key**: `constraint_scores` in return dictionary
3. **Score calculation**: Based on constraint scale, RHS magnitude, tightness

#### Where Constraint Names Originate:

1. **Already present**: Formula dictionary keys ARE constraint names
2. **In `_find_constraint_formulas`**: Returns list of constraint formula names
3. **Propagation**: These names flow to builder, then to solver

#### What Should Remain Untouched:

1. **Variable detection logic**: Decision variable identification must not change
2. **DSL parsing**: Existing DECISION/OBJECTIVE/BOUND detection must remain
3. **Formula classification**: Objective/constraint/bound classification logic
4. **Core detection algorithm**: `is_lp_problem` determination logic

#### Pseudo-Diff Snippets:

**OLD: `detect_lp_formulas` return**

```python
return {
    'objective': objective_formula,
    'constraints': constraint_formulas,  # <-- These are the names
    'bounds': bound_formulas,
    'variables': sorted(decision_vars),
    'is_lp_problem': is_lp_problem,
    'lp_formulas': lp_formulas,
    'dsl_structures': dsl_structures
}
```

**NEW (conceptual): With diagnostic scores**

```python
# After finding constraint formulas
constraint_scores = {}
for constraint_name in constraint_formulas:
    if constraint_name in formulas:
        formula = formulas[constraint_name]
        score = self._calculate_dominance_score(formula, scenario_context)
        constraint_scores[constraint_name] = score

return {
    'objective': objective_formula,
    'constraints': constraint_formulas,
    'constraint_scores': constraint_scores,  # <-- NEW FIELD
    'bounds': bound_formulas,
    'variables': sorted(decision_vars),
    'is_lp_problem': is_lp_problem,
    'lp_formulas': lp_formulas,
    'dsl_structures': dsl_structures
}
```

**NEW (conceptual): Score calculation method**

```python
def _calculate_dominance_score(
    self,
    formula: str,
    context: Dict[str, Any]
) -> float:
    """
    Calculate diagnostic dominance score for a constraint.

    Formula from v2.1: 0.5*scale + 0.3*rhs_mag + 0.2*(1/(abs(b_i)+1e-6))

    Returns:
        Score between 0 and 1 (higher = more likely dominant)
    """
    # Parse constraint to extract coefficients and RHS
    # Calculate scale (norm of coefficient vector)
    # Calculate RHS magnitude
    # Calculate tightness factor
    # Combine with weights

    return score  # Diagnostic only, not used for formulation
```

---

## SECTION 2 — END-TO-END FLOW (CODE LEVEL)

### DSL → Parser → Builder → Solver → Result

#### Data Structure Changes:

**Parser Output (`lp_spec`):**

```python
{
    'constraints': ['constraint_1', 'constraint_2', ...],  # Names
    'constraint_scores': {'constraint_1': 0.85, ...},     # NEW: Diagnostic
    # ... existing fields
}
```

**Builder Output (Matrices):**

```python
{
    'A_ub': [[...], [...]],          # Constraint coefficients
    'b_ub': [b1, b2, ...],           # RHS values
    'constraint_names': ['constraint_1', 'constraint_2', ...],  # NEW
    # ... existing fields
}
```

**Solver Input/Output:**

```python
# Input to solve()
solver.solve(
    c=c_vector,
    A_ub=A_ub_matrix,
    b_ub=b_ub_vector,
    constraint_names=constraint_names  # NEW PARAMETER
)

# Output from solve()
{
    'success': True,
    'x': [...],
    'fun': 123.45,
    'binding_constraints': ['constraint_1', 'constraint_3'],  # NEW
    # ... existing fields
}
```

#### Where Dominance Becomes Known:

1. **Parser phase**: Diagnostic scores calculated (heuristic only)
2. **Builder phase**: Constraint names preserved for explanation
3. **Solver phase**: TRUE binding constraints identified (post-solve)
4. **Result phase**: Binding constraints included in final output

#### Flow Diagram (Code Perspective):

```
DSL Formulas
    ↓
Parser.detect_lp_formulas()
    → extracts constraint names
    → calculates diagnostic scores (optional)
    ↓
Builder.build_from_formulas()
    → builds A_ub, b_ub matrices
    → preserves constraint names in order
    → (SIMULATE mode: creates β-adjusted matrices)
    ↓
Solver.solve()
    → solves LP problem
    → calls detect_binding_constraints()
    → uses adaptive tolerance: tol = tolerance * (1 + abs(b[i]))
    → maps indices to names (if provided)
    ↓
Result
    → includes binding_constraints with meaningful names
    → (SIMULATE mode: includes comparison of base vs β)
```

---

## SECTION 3 — EDGE CASE ANALYSIS

### 1️⃣ Multiple Binding Constraints

**Code Impact**: `detect_binding_constraints` must return list, not single
**Tolerance Handling**: Adaptive tolerance prevents false positives
**Implementation**: Loop through all constraints, collect those within tolerance
**Risk**: Could identify too many constraints as "binding" if tolerance too large

### 2️⃣ Equality Constraints

**Current State**: Only inequality constraints (A_ub, b_ub) supported
**Future Support**: `detect_binding_constraints` should handle A_eq, b_eq
**Code Change**: Add equality constraint detection parallel to inequality
**Tolerance**: Equality constraints use absolute tolerance (no scaling needed)

**Pseudo-code for future:**

```python
if A_eq is not None and b_eq is not None:
    residual_eq = A_eq @ x - b_eq
    for i, r in enumerate(residual_eq):
        if abs(r) <= self.tolerance:  # Absolute tolerance for equalities
            binding_eq.append(i)
```

### 3️⃣ Tolerance Scaling

**Issue**: Fixed tolerance fails with large RHS values
**Solution**: `tol = self.tolerance * (1 + abs(b[i]))`
**Code Location**: Inside `detect_binding_constraints` loop
**Validation Needed**: Test with RHS values spanning orders of magnitude
**Edge Cases**: b[i] = 0 → tol = self.tolerance (minimum)
**Risk**: Over-scaling with very large b[i] values

### 4️⃣ Large LP Scaling

**Performance**: O(m\*n) for m constraints, n variables
**Memory**: Need to store A_ub matrix (m×n) and residuals (m)
**Optimization**: Use numpy vectorized operations
**Code Impact**: Minimal - numpy @ operator handles large matrices efficiently
**Risk**: Memory usage with thousands of constraints

---

## SECTION 4 — RISK ANALYSIS

### Backward Compatibility

**High Risk Areas**:

1. **Solver.**init** signature change**: Adding `tolerance` parameter with default value
   - **Mitigation**: Default value preserves existing calls
   - **Impact**: None for existing code

2. **Solver.solve() return format**: Adding `binding_constraints` key
   - **Mitigation**: New key, doesn't affect existing key access
   - **Impact**: Existing code ignoring new key continues to work

3. **Builder.build_from_formulas() signature**: Adding `dominance_mode` parameter
   - **Mitigation**: Default value ("ANALYZE") preserves existing calls
   - **Impact**: None for existing code

**Safe Changes**:

1. Parser adding `constraint_scores` diagnostic field
2. Builder adding `constraint_names` field to output
3. New methods don't affect existing functionality

### Regression Risks

**Critical Risk**: Binding detection affecting solve results

- **Cause**: `detect_binding_constraints` called after solve, doesn't affect solution
- **Mitigation**: Post-processing only, no formulation changes

**Medium Risk**: Tolerance parameter affecting constraint feasibility checks

- **Cause**: `check_feasibility` method uses `self.tolerance`
- **Mitigation**: Ensure tolerance scaling consistent across methods

**Low Risk**: SIMULATE mode creating incorrect β matrices

- **Cause**: Only multiplies RHS (b_ub), not coefficients
- **Mitigation**: Clear documentation, only for analysis

### Maintainability Risks

**Complexity Increase**:

- New `detect_binding_constraints` method in solver
- Constraint name tracking through pipeline
- SIMULATE mode branching logic

**Documentation Need**:

- Clear separation: ANALYZE (default) vs SIMULATE (optional)
- Diagnostic scores vs true binding constraints
- Tolerance scaling behavior

**Testing Burden**:

- Need tests for binding detection with various tolerance values
- Need tests for constraint name propagation
- Need tests for SIMULATE mode comparison

---

## SECTION 5 — CHANGE PRIORITY

### 🔴 MUST (Critical for Production)

1. **Solver: Add tolerance parameter to **init\*\*\*\*
   - Required for adaptive binding detection
   - Backward compatible with default value

2. **Solver: Implement detect_binding_constraints()**
   - Core dominance logic
   - Adaptive tolerance: `tol = tolerance * (1 + abs(b[i]))`

3. **Solver: Integrate binding detection into solve()**
   - Add `binding_constraints` to result dict
   - Post-processing only, doesn't affect solution

4. **Builder: Preserve constraint names**
   - Track constraint formula names alongside matrices
   - Pass to solver for meaningful output

5. **Parser: Extract constraint names**
   - Already done (formula keys are names)
   - Ensure names flow through pipeline

### 🟡 SHOULD (Important for Usability)

1. **Builder: Implement SIMULATE mode**
   - Optional feature for sensitivity analysis
   - Create β-adjusted matrices (RHS × 1.5)

2. **Solver: Support constraint_names parameter**
   - Map binding indices to meaningful names
   - Essential for KPI explanation

3. **Comparison function for SIMULATE mode**
   - Compare base vs β results
   - Objective difference, solution difference metrics

### 🟢 OPTIONAL (Nice-to-have)

1. **Parser: Diagnostic score calculation**
   - Heuristic dominance prediction
   - UI/debug purposes only, not used for formulation

2. **Equality constraint support in binding detection**
   - Future enhancement
   - Requires changes to detect_binding_constraints()

3. **Advanced tolerance tuning**
   - Beyond simple scaling
   - Problem-specific tolerance strategies

---

## IMPLEMENTATION NOTES

### Critical Dependencies Between Files:

1. **Parser → Builder**: Constraint names flow from parser's `constraints` list to builder
2. **Builder → Solver**: `constraint_names` array must match `A_ub` row order
3. **Solver → Result**: Binding indices mapped to names before returning
4. **SIMULATE mode**: Requires builder to return both base and β matrices

### Integration Points Requiring Coordination:

1. **Tolerance consistency**: Same `tolerance` parameter used in:
   - `LPSolver.__init__()`
   - `detect_binding_constraints()` adaptive scaling
   - `check_feasibility()` method
2. **Constraint name propagation chain**:

   ```
   Parser.constraints (list of names)
   ↓
   Builder.constraint_names (preserved order)
   ↓
   Solver.solve(constraint_names=...)
   ↓
   Result.binding_constraints (meaningful names)
   ```

3. **SIMULATE mode data flow**:
   ```
   Builder.build_from_formulas(dominance_mode="SIMULATE")
   → returns {'base': ..., 'beta': ..., 'mode': 'SIMULATE'}
   ↓
   User code solves both and compares
   ```

### Testing Strategy Recommendations:

1. **Unit tests for `detect_binding_constraints`**:
   - Test with known binding constraints
   - Test tolerance scaling with various RHS values
   - Test empty/missing inputs

2. **Integration tests for name propagation**:
   - End-to-end test with sample formulas
   - Verify constraint names preserved through pipeline
   - Verify binding constraints returned with names

3. **SIMULATE mode tests**:
   - Verify β matrices correctly scaled (RHS × 1.5)
   - Verify coefficients unchanged
   - Test comparison function

### Performance Considerations:

1. **Binding detection overhead**: O(m) for m constraints (after O(m×n) solve)
2. **Memory for constraint names**: Minimal (list of strings)
3. **SIMULATE mode cost**: 2× solve time + comparison
4. **Adaptive tolerance calculation**: Negligible overhead

## CONCLUSION

The v2.1 dominance strategy integration requires coordinated changes across three core files while maintaining the validated architecture principles:

### Key Architectural Validations Confirmed:

1. ✅ **Dominance in solver** - Binding constraints determined post-solve
2. ✅ **Parser diagnostic only** - Scores for UI, not formulation
3. ✅ **Builder formulation unchanged** - Production safety maintained
4. ✅ **Solver single source of truth** - True binding from numerical solution

### Implementation Complexity Assessment:

**Low Risk Changes**:

- Adding `tolerance` parameter with default value
- Adding `binding_constraints` to result dict (new key)
- Adding `constraint_names` to builder output (new key)

**Medium Complexity Changes**:

- Implementing `detect_binding_constraints()` with adaptive tolerance
- Constraint name tracking through pipeline
- SIMULATE mode branching in builder

**Optional Enhancements**:

- Parser diagnostic scores
- Equality constraint support
- Advanced tolerance tuning

### Recommended Implementation Order:

1. **Phase 1 (Core)**: Solver tolerance + binding detection
2. **Phase 2 (Essential)**: Constraint name infrastructure
3. **Phase 3 (Analytical)**: SIMULATE mode for sensitivity analysis
4. **Phase 4 (Optional)**: Parser diagnostic scores

### Final Technical Assessment:

The v2.1 strategy represents a **production-ready, minimally invasive integration** that:

- Adds valuable analytical capability (binding constraint identification)
- Maintains backward compatibility (default parameters preserve existing behavior)
- Provides meaningful business insights (constraint names for KPI explanation)
- Enables sensitivity analysis (SIMULATE mode for what-if scenarios)
- Respects architectural boundaries (no formulation changes in production)

The code-level analysis shows clear integration points with manageable complexity and well-defined dependencies between components.
