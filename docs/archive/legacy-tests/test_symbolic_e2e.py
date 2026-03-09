"""
Full E2E Test: Symbolic Structure -> DSL -> AST -> Canonical -> Matrix -> Solver -> Result

Symbolic structure:
CM_J        P_J − C_J
CM_NORM     NORM(vector(CM_J))
SAFE_X_MIN  X0_J − r0*(CM_J/CM_NORM)
SAFE_X_MAX  X0_J + r0*(CM_J/CM_NORM)

Test data:
N = 3
P = [700,1120,4480]
C = [280,420,2240]
F = 14000
XMIN = [6.66,4,1.25]
XMAX = [26.66,16,5]
"""

import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ast_expression_parser import parse_expression
from constraint_extractor import extract_constraints, Constraint
from dsl_parser import parse_dsl, DSLInfo
from matrix_builder_v3 import MatrixBuilderV3
from lp_solver_engine import LPSolverEngine


def calculate_cm_values():
    """Calculate CM values from test data."""
    P = [700, 1120, 4480]
    C = [280, 420, 2240]
    
    # CM_J = P_J - C_J
    CM = [p - c for p, c in zip(P, C)]
    
    # CM_NORM = sqrt(CM1^2 + CM2^2 + CM3^2)
    CM_NORM = math.sqrt(sum(c**2 for c in CM))
    
    return CM, CM_NORM


def test_symbolic_e2e():
    """Full E2E test with symbolic structure."""
    print("=" * 80)
    print("FULL E2E TEST: SYMBOLIC STRUCTURE")
    print("=" * 80)
    
    # Calculate CM values
    CM, CM_NORM = calculate_cm_values()
    print(f"\nCalculated values:")
    print(f"CM1 = {CM[0]:.2f} (700 - 280)")
    print(f"CM2 = {CM[1]:.2f} (1120 - 420)")
    print(f"CM3 = {CM[2]:.2f} (4480 - 2240)")
    print(f"CM_NORM = {CM_NORM:.4f}")
    
    # Build DSL with current engine format
    dsl_code = f"""
    DECISION(x,size=3)
    DECISION(r)
    
    # Note: In current engine, we need to define CM values as constants
    # The engine doesn't support arithmetic in DECISION or BOUND statements
    # So we'll use the calculated values directly in constraints
    """
    
    # Parse DSL
    print("\n1. DSL PARSING")
    print("-" * 40)
    
    dsl_lines = [line.strip() for line in dsl_code.strip().split('\n') if line.strip()]
    all_decisions = []
    all_bounds = []
    all_objectives = []
    
    for line in dsl_lines:
        if line.startswith('DECISION'):
            dsl_info = parse_dsl(line)
            all_decisions.extend(dsl_info.decisions)
    
    # Add bounds manually (current engine doesn't support vector bounds)
    # We need to add bounds for each component
    from dsl_parser import DSLBound
    XMIN = [6.66, 4, 1.25]
    XMAX = [26.66, 16, 5]
    
    for i in range(3):
        all_bounds.append(DSLBound(variable_name=f'x{i+1}', lower=XMIN[i], upper=XMAX[i]))
    
    # Bound for r
    all_bounds.append(DSLBound(variable_name='r', lower=0.0, upper=None))
    
    # Objective: CM1*x1 + CM2*x2 + CM3*x3
    # In current engine, we need to parse the objective expression
    from dsl_parser import DSLObjective
    from ast_expression_parser import parse_expression
    
    # Create objective expression
    objective_expr = parse_expression(f"{CM[0]}*x1 + {CM[1]}*x2 + {CM[2]}*x3")
    all_objectives.append(DSLObjective(expression=objective_expr))
    
    dsl_info = DSLInfo(
        decisions=all_decisions,
        bounds=all_bounds,
        objectives=all_objectives
    )
    
    print(f"Decisions: {[d.variable_name for d in dsl_info.decisions]}")
    print(f"Objectives: {[o.expression for o in dsl_info.objectives]}")
    print(f"Bounds: {[(b.variable_name, b.lower, b.upper) for b in dsl_info.bounds]}")
    
    print("\n2. CONSTRAINT EXTRACTION")
    print("-" * 40)
    
    # Main constraint: -(CM1*x1+CM2*x2+CM3*x3)+SQRT(CM1^2+CM2^2+CM3^2)*r <= -14000
    # Which is: -CM1*x1 - CM2*x2 - CM3*x3 + CM_NORM*r <= -F
    constraint_expr = f"-({CM[0]}*x1 + {CM[1]}*x2 + {CM[2]}*x3) + {CM_NORM}*r <= -14000"
    
    # Also need the safety constraints: xj - r >= XMIN_j and xj + r <= XMAX_j
    constraints_code = [constraint_expr]
    
    for i in range(3):
        constraints_code.append(f"x{i+1} - r >= {XMIN[i]}")
        constraints_code.append(f"x{i+1} + r <= {XMAX[i]}")
    
    # Extract constraints
    constraints = []
    for expr in constraints_code:
        extracted = extract_constraints(expr)
        constraints.extend(extracted)
        print(f"  {expr}")
        for c in extracted:
            print(f"    -> {c.coefficients} {c.sense} {c.constant}")
    
    print("\n3. MATRIX BUILDING")
    print("-" * 40)
    
    # Build matrices
    builder = MatrixBuilderV3()
    matrices = builder.build_matrices(constraints, dsl_info)
    
    print(f"Variables: {matrices['variables']}")
    print(f"Objective coefficients (c): {matrices['c']}")
    print(f"Constraint matrix (A_ub): {len(matrices['A_ub'])} rows")
    print(f"Constraint vector (b_ub): {len(matrices['b_ub'])} elements")
    print(f"Bounds: {matrices['bounds']}")
    
    print("\n4. SOLVER EXECUTION")
    print("-" * 40)
    
    # Solve using LPSolverEngine (maximize objective)
    engine = LPSolverEngine()
    result = engine.solve_complete(matrices, objective_type="maximize")
    
    print(f"Status: {result['status']}")
    print(f"Objective: {result['objective']}")
    print(f"Solution: {result['solution']}")
    
    print("\n5. USEFULNESS RANGE (Directional)")
    print("-" * 40)
    
    # Calculate directional usefulness range: xj* ± r*(hj/||h||)
    # Where hj = CM_j and ||h|| = CM_NORM
    r_star = result['solution']['r']
    
    directional_ranges = {}
    for i in range(3):
        xj_star = result['solution'][f'x{i+1}']
        hj = CM[i]
        directional_offset = r_star * (hj / CM_NORM)
        
        low = xj_star - directional_offset
        high = xj_star + directional_offset
        
        directional_ranges[f'x{i+1}'] = (low, high)
        print(f"x{i+1}* = {xj_star:.6f}")
        print(f"  hj/||h|| = {hj:.2f}/{CM_NORM:.4f} = {hj/CM_NORM:.6f}")
        print(f"  r* * (hj/||h||) = {r_star:.6f} * {hj/CM_NORM:.6f} = {directional_offset:.6f}")
        print(f"  Range: [{low:.6f}, {high:.6f}]")
    
    # Also compute standard usefulness range for comparison
    if result['usefulness_range']:
        print(f"\nStandard usefulness range (xj* ± r*):")
        for var, (low, high) in result['usefulness_range'].items():
            if var.startswith('x'):
                print(f"  {var}: [{low:.6f}, {high:.6f}]")
    
    print("\n6. VALIDATION")
    print("-" * 40)
    
    # Verify LP feasibility and optimality
    assert result['status'] == "optimal", f"Expected optimal, got {result['status']}"
    assert result['objective'] is not None, "Objective should not be None"
    
    # Verify solution satisfies bounds
    for i in range(3):
        x_val = result['solution'][f'x{i+1}']
        assert XMIN[i] - 0.001 <= x_val <= XMAX[i] + 0.001, \
            f"x{i+1} = {x_val} not in [{XMIN[i]}, {XMAX[i]}]"
    
    # Verify r >= 0
    assert result['solution']['r'] >= -0.001, f"r = {result['solution']['r']} should be >= 0"
    
    # Verify main constraint
    lhs = -sum(CM[i] * result['solution'][f'x{i+1}'] for i in range(3)) + CM_NORM * result['solution']['r']
    assert lhs <= -14000 + 0.001, f"Main constraint violated: {lhs} <= -14000"
    
    print("Pass All validation checks passed!")
    
    return {
        'status': result['status'],
        'objective': result['objective'],
        'solution': result['solution'],
        'usefulness_range': result['usefulness_range'],
        'directional_usefulness_range': directional_ranges
    }


def evaluate_dsl_compatibility():
    """Evaluate current DSL and suggest improvements."""
    print("\n" + "=" * 80)
    print("DSL COMPATIBILITY EVALUATION")
    print("=" * 80)
    
    print("\nCurrent DSL Limitations:")
    print("1. No support for arithmetic in DECISION or BOUND statements")
    print("2. No vector bounds syntax (BOUND(x,[min],[max]))")
    print("3. No constant definitions within DSL")
    print("4. No support for CM_J = P_J - C_J expressions")
    print("5. No NORM() function support")
    
    print("\nImproved DSL Proposal:")
    print("-" * 40)
    
    improved_dsl = """
    # Constants definition
    CONSTANT P = [700, 1120, 4480]
    CONSTANT C = [280, 420, 2240]
    CONSTANT F = 14000
    CONSTANT XMIN = [6.66, 4, 1.25]
    CONSTANT XMAX = [26.66, 16, 5]
    
    # Derived values with expressions
    CM = P - C  # Vector subtraction
    CM_NORM = NORM(CM)  # Norm function
    
    # Decisions
    DECISION(x, size=3)
    DECISION(r)
    
    # Objective with vector dot product
    OBJECTIVE(DOT(CM, x))
    
    # Vector bounds
    BOUND(x, XMIN, XMAX)
    BOUND(r, 0, None)
    
    # Constraint with norm expression
    CONSTRAINT: -DOT(CM, x) + CM_NORM * r <= -F
    
    # Safety constraints (auto-generated from bounds and r)
    SAFETY(x, r)  # Automatically generates xj - r >= XMIN_j and xj + r <= XMAX_j
    """
    
    print(improved_dsl)
    
    print("\nKey Improvements:")
    print("1. CONSTANT keyword for defining constants")
    print("2. Vector arithmetic support (P - C)")
    print("3. NORM() function for vector norms")
    print("4. DOT() function for dot products")
    print("5. Vector bounds syntax")
    print("6. SAFETY() macro for automatic safety constraints")
    print("7. Expression support in all DSL elements")
    
    return improved_dsl


def main():
    """Run full E2E test and DSL evaluation."""
    print("FULL E2E TEST WITH DSL EVALUATION")
    print("=" * 80)
    
    try:
        # Run E2E test
        result = test_symbolic_e2e()
        
        print("\n" + "=" * 80)
        print("FINAL RESULT")
        print("=" * 80)
        
        print(f"Status: {result['status']}")
        print(f"Objective: {result['objective']:.6f}")
        print(f"\nSolution:")
        for var, val in result['solution'].items():
            print(f"  {var}: {val:.6f}")
        
        print(f"\nDirectional Usefulness Ranges (xj* ± r*(hj/||h||)):")
        for var, (low, high) in result['directional_usefulness_range'].items():
            print(f"  {var}: [{low:.6f}, {high:.6f}]")
        
        # Evaluate DSL
        improved_dsl = evaluate_dsl_compatibility()
        
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("The current DSL engine works but has limitations for symbolic problems.")
        print("Recommended to implement the improved DSL features for better usability.")
        
        return True
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)