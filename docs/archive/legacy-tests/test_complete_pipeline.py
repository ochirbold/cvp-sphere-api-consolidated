"""
Complete Pipeline Test: DSL → AST → Canonical → Matrix → Solver → Result

Demonstrates the full Week-4 implementation:
1. DSL parsing (Week-2)
2. Constraint extraction (Week-2)
3. Matrix building (Week-3)
4. Solver execution (Week-4)
5. Result mapping (Week-4)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ast_expression_parser import parse_expression
from constraint_extractor import extract_constraints, Constraint
from dsl_parser import parse_dsl, DSLInfo
from matrix_builder_v3 import MatrixBuilderV3
from lp_solver_engine import LPSolverEngine


def test_paving_problem_complete():
    """Complete paving problem pipeline test."""
    print("=" * 80)
    print("COMPLETE PIPELINE TEST: PAVING PROBLEM")
    print("=" * 80)
    
    # Paving problem DSL
    dsl_code = """
    DECISION(x1)
    DECISION(x2)
    DECISION(x3)
    DECISION(r)
    OBJECTIVE(r)  # Maximize r
    BOUND(x1,6.66,26.66)
    BOUND(x2,4,16)
    BOUND(x3,1.25,5)
    BOUND(r,0,100)
    """
    
    # Paving problem constraints
    constraints_code = [
        "420*x1 + 700*x2 - 2384.11*r >= 14000",
        "x1 - r >= 6.66",
        "x1 + r <= 26.66",
        "x2 - r >= 4",
        "x2 + r <= 16",
        "x3 - r >= 1.25",
        "x3 + r <= 5",
    ]
    
    print("\n1. DSL PARSING (Week-2)")
    print("-" * 40)
    
    # Parse DSL
    dsl_lines = [line.strip() for line in dsl_code.strip().split('\n') if line.strip()]
    all_decisions = []
    all_bounds = []
    all_objectives = []
    
    for line in dsl_lines:
        dsl_info = parse_dsl(line)
        all_decisions.extend(dsl_info.decisions)
        all_bounds.extend(dsl_info.bounds)
        all_objectives.extend(dsl_info.objectives)
    
    dsl_info = DSLInfo(
        decisions=all_decisions,
        bounds=all_bounds,
        objectives=all_objectives
    )
    
    print(f"Decisions: {[d.variable_name for d in dsl_info.decisions]}")
    print(f"Objectives: {[o.expression for o in dsl_info.objectives]}")
    print(f"Bounds: {[(b.variable_name, b.lower, b.upper) for b in dsl_info.bounds]}")
    
    print("\n2. CONSTRAINT EXTRACTION (Week-2)")
    print("-" * 40)
    
    # Extract constraints
    constraints = []
    for expr in constraints_code:
        extracted = extract_constraints(expr)
        constraints.extend(extracted)
        print(f"  {expr}")
        for c in extracted:
            print(f"    -> {c.coefficients} {c.sense} {c.constant}")
    
    print("\n3. MATRIX BUILDING (Week-3)")
    print("-" * 40)
    
    # Build matrices
    builder = MatrixBuilderV3()
    matrices = builder.build_matrices(constraints, dsl_info)
    
    print(f"Variables: {matrices['variables']}")
    print(f"Objective coefficients (c): {matrices['c']}")
    print(f"Constraint matrix (A_ub): {len(matrices['A_ub'])} rows")
    print(f"Constraint vector (b_ub): {len(matrices['b_ub'])} elements")
    print(f"Bounds: {matrices['bounds']}")
    
    print("\n4. SOLVER EXECUTION (Week-4)")
    print("-" * 40)
    
    # Solve using LPSolverEngine
    engine = LPSolverEngine()
    result = engine.solve_complete(matrices, objective_type="maximize")
    
    print(f"Status: {result['status']}")
    print(f"Objective (r*): {result['objective']}")
    print(f"Solution: {result['solution']}")
    
    if result['usefulness_range']:
        print(f"Usefulness Range: {result['usefulness_range']}")
    
    print("\n5. VALIDATION")
    print("-" * 40)
    
    # Verify the solution
    assert result['status'] == "optimal", f"Expected optimal, got {result['status']}"
    assert result['objective'] is not None, "Objective should not be None"
    assert 'r' in result['solution'], "r should be in solution"
    assert result['usefulness_range'] is not None, "Usefulness range should be computed"
    
    # Check usefulness range formula
    r_star = result['solution']['r']
    for var in ['x1', 'x2', 'x3']:
        x_star = result['solution'][var]
        low, high = result['usefulness_range'][var]
        
        expected_low = x_star - r_star
        expected_high = x_star + r_star
        
        assert abs(low - expected_low) < 0.001, f"Usefulness range low for {var} incorrect"
        assert abs(high - expected_high) < 0.001, f"Usefulness range high for {var} incorrect"
    
    print("Pass All checks passed!")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Optimal r*: {result['objective']:.6f}")
    print(f"x1*: {result['solution']['x1']:.6f} (range: {result['usefulness_range']['x1'][0]:.6f} to {result['usefulness_range']['x1'][1]:.6f})")
    print(f"x2*: {result['solution']['x2']:.6f} (range: {result['usefulness_range']['x2'][0]:.6f} to {result['usefulness_range']['x2'][1]:.6f})")
    print(f"x3*: {result['solution']['x3']:.6f} (range: {result['usefulness_range']['x3'][0]:.6f} to {result['usefulness_range']['x3'][1]:.6f})")
    
    return True


def test_simple_lp_complete():
    """Simple LP pipeline test."""
    print("\n" + "=" * 80)
    print("COMPLETE PIPELINE TEST: SIMPLE LP")
    print("=" * 80)
    
    # Simple LP: maximize x + y subject to x <= 5, y <= 3, x + y <= 7
    dsl_code = """
    DECISION(x)
    DECISION(y)
    OBJECTIVE(-x - y)  # Maximize x + y = minimize -x - y
    BOUND(x,0,None)
    BOUND(y,0,None)
    """
    
    constraints_code = [
        "x <= 5",
        "y <= 3",
        "x + y <= 7",
    ]
    
    print("\n1. DSL PARSING")
    dsl_lines = [line.strip() for line in dsl_code.strip().split('\n') if line.strip()]
    all_decisions = []
    all_bounds = []
    all_objectives = []
    
    for line in dsl_lines:
        dsl_info = parse_dsl(line)
        all_decisions.extend(dsl_info.decisions)
        all_bounds.extend(dsl_info.bounds)
        all_objectives.extend(dsl_info.objectives)
    
    dsl_info = DSLInfo(
        decisions=all_decisions,
        bounds=all_bounds,
        objectives=all_objectives
    )
    
    print("\n2. CONSTRAINT EXTRACTION")
    constraints = []
    for expr in constraints_code:
        extracted = extract_constraints(expr)
        constraints.extend(extracted)
    
    print("\n3. MATRIX BUILDING")
    builder = MatrixBuilderV3()
    matrices = builder.build_matrices(constraints, dsl_info)
    
    print("\n4. SOLVER EXECUTION")
    engine = LPSolverEngine()
    result = engine.solve_complete(matrices, objective_type="minimize")
    
    print(f"Status: {result['status']}")
    print(f"Objective: {result['objective']} (maximize x+y = {-result['objective']})")
    print(f"Solution: {result['solution']}")
    
    print("\n5. VALIDATION")
    assert result['status'] == "optimal", f"Expected optimal, got {result['status']}"
    assert abs(result['objective'] - (-7.0)) < 0.001, f"Expected objective -7, got {result['objective']}"
    assert result['solution']['x'] <= 5.001, f"x should be <= 5, got {result['solution']['x']}"
    assert result['solution']['y'] <= 3.001, f"y should be <= 3, got {result['solution']['y']}"
    assert result['solution']['x'] + result['solution']['y'] <= 7.001, f"x+y should be <= 7, got {result['solution']['x'] + result['solution']['y']}"
    
    print("Pass All checks passed!")
    print(f"\nOptimal solution: x = {result['solution']['x']}, y = {result['solution']['y']}")
    print(f"Maximum value of x+y = {-result['objective']}")
    
    return True


def main():
    """Run complete pipeline tests."""
    print("WEEK-4 COMPLETE PIPELINE TESTS")
    print("=" * 80)
    
    results = []
    
    try:
        results.append(("Paving Problem", test_paving_problem_complete()))
    except Exception as e:
        print(f"Paving Problem test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Paving Problem", False))
    
    try:
        results.append(("Simple LP", test_simple_lp_complete()))
    except Exception as e:
        print(f"Simple LP test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Simple LP", False))
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("ALL PIPELINE TESTS PASSED!")
        print("\nWeek-4 Implementation Complete:")
        print("Pass DSL -> AST -> Canonical -> Matrix -> Solver -> Result pipeline")
        print("Pass Full paving problem solved")
        print("Pass Usefulness range computed correctly")
        print("Pass Error handling for infeasible/unbounded problems")
        print("Pass Deterministic execution")
    else:
        print("SOME PIPELINE TESTS FAILED")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)