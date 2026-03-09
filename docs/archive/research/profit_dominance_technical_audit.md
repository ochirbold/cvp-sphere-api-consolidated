# Profit Dominance v2.1 Technical Architecture Audit

## Executive Summary

This audit analyzes how the v2.1 dominance strategy integrates with the existing LP optimization pipeline. The analysis focuses on architectural impact, change requirements, and risk assessment without providing implementation code.

## SECTION 1 — FILE-BY-FILE IMPACT ANALYSIS

### 📄 lp_solver.py

#### Impacted Parts:

1. **Class Initialization**: The `LPSolver.__init__` method requires modification to accept and store a tolerance parameter for binding constraint detection.

2. **Solve Method Integration**: The core `solve()` method needs architectural extension to incorporate binding constraint detection between obtaining the raw solver result and formatting the final output.

3. **Result Structure**: The result dictionary returned by `solve()` and `solve_from_matrices()` requires extension to include binding constraint information.

#### Conceptual Additions Required:

- A binding constraint detection capability that operates on the solved solution vector
- Adaptive tolerance logic that scales with constraint right-hand-side magnitudes
- Optional constraint name mapping for meaningful KPI reporting

#### Conceptual Modifications Required:

- Extension of the result formatting pipeline to include binding constraint data
- Potential modification of error handling to accommodate new detection logic

#### Untouched Parts:

- The core solving logic using `scipy.optimize.linprog` remains unchanged
- Input validation and dimension checking remain independent
- The fundamental solving algorithm and optimization logic are preserved

### 📄 lp_matrix_builder_deterministic_complete.py

#### Change Requirements:

1. **Configuration Propagation**: The builder needs to accept and propagate dominance mode configuration from the scenario context to downstream components.

2. **Constraint Metadata Preservation**: The builder must preserve constraint ordering and optionally constraint names for meaningful reporting.

3. **Simulation Mode Infrastructure**: Architectural support for creating test matrices with β adjustment while maintaining original formulation integrity.

#### Logical Change Locations:

- Initialization method to read dominance mode from scenario context
- Matrix construction completion phase to optionally create simulation matrices
- Result packaging to include constraint metadata if available

#### Risks if Changed Incorrectly:

- **Formulation Corruption**: If simulation logic incorrectly modifies production matrices
- **Metadata Loss**: If constraint ordering or names are not preserved, binding detection becomes meaningless
- **Configuration Leakage**: If dominance mode affects production solving behavior

#### Minimal Change Principle:

The builder's core responsibility remains unchanged: deterministic matrix construction. Dominance-related changes are additive and optional.

### 📄 lp_model_parser.py

#### Role in Dominance Pipeline:

The parser serves a **diagnostic and metadata** role only, not a computational one.

#### Optional Conceptual Additions:

- Constraint scoring for UI/debug visualization purposes
- Constraint name extraction from formula expressions
- Metadata enrichment of the LP specification dictionary

#### What Must NOT Be Done:

- **No Formulation Decisions**: Parser scores must not influence matrix construction
- **No Binding Prediction**: Parser cannot predict binding constraints (only solver can determine this)
- **No Algorithmic Changes**: Core parsing logic for DSL detection remains unchanged

#### Architectural Position:

The parser operates upstream of dominance determination. Its role is preparatory, not determinative.

## SECTION 2 — FULL PIPELINE IMPACT ANALYSIS

### Pipeline: DSL → Parser → Builder → Solver → Output

#### Step 1: DSL to Parser

- **Impact**: Minimal. Parser may optionally extract constraint names and compute diagnostic scores.
- **Dominance Relevance**: None at this stage. Dominance cannot be known from formulas alone.

#### Step 2: Parser to Builder

- **Impact**: Constraint metadata (names, optional scores) may be passed forward.
- **Critical Principle**: Builder receives but does not act on scores for formulation decisions.

#### Step 3: Builder to Solver

- **Impact**: Builder may pass constraint names/ordering to solver for meaningful reporting.
- **Simulation Path**: Builder may create alternative matrices for simulation mode while preserving original.

#### Step 4: Solver Computation

- **Where Dominance Becomes Known**: **EXCLUSIVELY HERE**. Binding constraints can only be determined after the solution vector is computed.
- **Architectural Truth**: Solver is the single source of dominance truth.

#### Step 5: Output Enhancement

- **Impact**: Result dictionary enriched with binding constraint information.
- **KPI Layer**: Binding constraints with meaningful names enable explanation capabilities.

### Where Dominance Must NOT Be Computed:

1. **Parser**: Cannot compute binding constraints (lacks solution vector)
2. **Builder**: Cannot compute binding constraints (lacks solver capability)
3. **Upstream Components**: Any dominance prediction is heuristic only, not truth

## SECTION 3 — RISK & SIDE EFFECT ANALYSIS

### 1️⃣ Backward Compatibility Risks

#### Low Risk Areas:

- **Result Dictionary Extension**: Adding new fields (`binding_constraints`) doesn't break existing code that doesn't use them
- **Optional Features**: Simulation mode and diagnostic scores are opt-in
- **Default Behavior**: ANALYZE mode with formulation untouched preserves existing behavior

#### Medium Risk Areas:

- **Tolerance Parameter Addition**: Changing `LPSolver.__init__` signature affects all instantiations
- **Mitigation**: Provide default value and maintain existing call patterns

### 2️⃣ Numerical Stability Risks

#### Adaptive Tolerance Algorithm:

- **Risk**: `tol = tolerance * (1 + abs(b[i]))` may produce inappropriate tolerances for very large b values
- **Mitigation**: Implement bounds checking and logarithmic scaling if needed
- **Testing Requirement**: Extensive validation across constraint magnitude ranges

#### Binding Detection Consistency:

- **Risk**: Different tolerance strategies may produce inconsistent binding sets
- **Mitigation**: Document tolerance behavior and provide configuration options

### 3️⃣ Performance Impact

#### Computational Overhead:

- **Binding Detection**: O(n\*m) operation where n=constraints, m=variables
- **Impact**: Negligible for typical problem sizes compared to solving time
- **Memory**: Additional storage for constraint names and binding sets

#### Simulation Mode Impact:

- **Double Solving**: Requires solving both base and β-adjusted problems
- **Mitigation**: Simulation is optional and for analysis only

### 4️⃣ Debugging Complexity

#### New Failure Modes:

- **Binding Detection Errors**: New code path with potential numerical issues
- **Metadata Propagation**: Constraint names may not align with matrices
- **Simulation Mode**: Additional complexity for what-if analysis

#### Mitigation Strategies:

- **Comprehensive Logging**: Debug output for dominance-related operations
- **Validation Checks**: Verify constraint name-array alignment
- **Graceful Degradation**: Fall back to indices if names unavailable

## SECTION 4 — CHANGE PRIORITY CLASSIFICATION

### 🔴 MUST (Critical for Core Functionality)

1. **Solver Tolerance Parameter**: Add to `LPSolver.__init__` for binding detection
2. **Binding Detection Integration**: Incorporate into solver's result pipeline
3. **Result Dictionary Extension**: Add `binding_constraints` field to results
4. **Constraint Order Preservation**: Ensure consistent constraint indexing across pipeline

### 🟡 SHOULD (Important for Usability)

1. **Constraint Name Infrastructure**: Collect and propagate meaningful constraint names
2. **Adaptive Tolerance Implementation**: Scale-aware binding detection
3. **Configuration Propagation**: Dominance mode from context to components
4. **Error Handling**: Graceful degradation for missing metadata

### 🟢 OPTIONAL (Enhanced Capabilities)

1. **Parser Diagnostic Scores**: Heuristic scoring for UI/debug purposes
2. **Simulation Mode**: Complete β sensitivity analysis framework
3. **Equality Constraint Support**: Extend binding detection to A_eq constraints
4. **Advanced Comparison Metrics**: Sophisticated simulation result analysis

## Architectural Principles Validation

### ✅ Confirmed Valid:

1. **Single Source of Truth**: Solver exclusively determines binding constraints
2. **Formulation Integrity**: Builder does not modify production matrices
3. **Diagnostic Separation**: Parser scores are informational only
4. **Optional Enhancement**: All new features are additive, not replacement

### ⚠️ Implementation Guardrails:

1. **Default Safety**: ANALYZE mode with formulation untouched must be default
2. **Metadata Consistency**: Constraint indexing must be preserved throughout pipeline
3. **Numerical Robustness**: Adaptive tolerance must handle edge cases
4. **Backward Compatibility**: Existing code must continue to work unchanged

## Conclusion

The v2.1 dominance strategy represents a **minimally invasive, architecturally sound** enhancement to the existing LP pipeline. The changes are:

1. **Concentrated**: Primarily in the solver, where dominance truth resides
2. **Additive**: New capabilities without replacing existing functionality
3. **Optional**: Enhanced features require explicit configuration
4. **Safe**: Core formulation and solving logic remain untouched

The architectural impact is well-contained, with clear boundaries between diagnostic capabilities (parser), formulation integrity (builder), and dominance determination (solver). This separation of concerns ensures maintainability while enabling valuable KPI explanation capabilities.
