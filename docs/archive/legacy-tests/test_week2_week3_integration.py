"""
Test Week-2 + Week-3 Integration with Paving Problem

This test validates the complete pipeline:
1. Week-2: Parse DSL and extract constraints
2. Week-2: Transform to canonical form
3. Week-3: Build matrices for solver
4. Validate with paving problem
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ast_expression_parser import parse_expression
from constraint_extractor import extract_constraints, Constraint
from dsl_parser import parse_dsl, DSLInfo
from matrix_builder_v3 import MatrixBuilderV3


def test_paving_problem_complete():
    """Test complete paving problem pipeline."""
    print("=" * 60)
    print("Paving Problem - Complete Pipeline Test")
    print("=" * 60)
    
    # Paving problem constraints
    constraint_expressions = [
        "420*x1 + 700*x2 - 2384.11*r >= 14000",
        "x1 - r >= 6.66",
        "x1 + r <= 26.66",
        "x2 - r >= 4",
        "x2 + r <= 16",
        "x3 - r >= 1.25",
        "x3 + r <= 5",
    ]
    
    # Paving problem DSL functions
    dsl_expressions = [
        "DECISION(x1)",
        "DECISION(x2)",
        "DECISION(x3)",
        "DECISION(r)",
        "OBJECTIVE(r)",
        "BOUND(x1,6.66,26.66)",
        "BOUND(x2,4,16)",
        "BOUND(x3,1.25,5)",
        "BOUND(r,0,100)",
    ]
    
    # Step 1: Extract constraints from expressions
    print("\nStep 1: Extracting constraints...")
    constraints = []
    for expr in constraint_expressions:
        extracted = extract_constraints(expr)
        constraints.extend(extracted)
        print(f"  {expr}")
        for c in extracted:
            print(f"    -> {c}")
    
    print(f"\nTotal constraints: {len(constraints)}")
    
    # Step 2: Parse DSL functions
    print("\nStep 2: Parsing DSL functions...")
    all_decisions = []
    all_bounds = []
    all_objectives = []
    
    for expr in dsl_expressions:
        dsl_info = parse_dsl(expr)
        all_decisions.extend(dsl_info.decisions)
        all_bounds.extend(dsl_info.bounds)
        all_objectives.extend(dsl_info.objectives)
        print(f"  {expr}")
    
    # Create DSLInfo object
    dsl_info = DSLInfo(
        decisions=all_decisions,
        bounds=all_bounds,
        objectives=all_objectives
    )
    
    print(f"\nDSL Summary:")
    print(f"  Decisions: {len(dsl_info.decisions)}")
    print(f"  Bounds: {len(dsl_info.bounds)}")
    print(f"  Objectives: {len(dsl_info.objectives)}")
    
    # Step 3: Build matrices using Week-3 MatrixBuilderV3
    print("\nStep 3: Building matrices with MatrixBuilderV3...")
    builder = MatrixBuilderV3()
    matrices = builder.build_matrices(constraints, dsl_info)
    
    # Step 4: Validate matrices
    print("\nStep 4: Matrix Validation")
    print(f"  Variables: {matrices['variables']}")
    print(f"  Number of variables: {len(matrices['c'])}")
    print(f"  Objective vector (c): {matrices['c']}")
    print(f"  Number of constraints: {len(matrices['A_ub'])}")
    print(f"  Bounds: {matrices['bounds']}")
    
    # Check dimensions
    assert len(matrices['c']) == len(matrices['variables']), "c vector length mismatch"
    assert len(matrices['bounds']) == len(matrices['variables']), "bounds length mismatch"
    if matrices['A_ub']:
        assert len(matrices['A_ub']) == len(matrices['b_ub']), "A_ub/b_ub length mismatch"
        for i, row in enumerate(matrices['A_ub']):
            assert len(row) == len(matrices['variables']), f"Row {i} length mismatch"
    
    # Check paving problem specifics
    print("\nStep 5: Paving Problem Validation")
    
    # Variables should be ['x1', 'x2', 'x3', 'r'] (sorted)
    expected_vars = ['x1', 'x2', 'x3', 'r']
    assert matrices['variables'] == expected_vars, f"Expected variables {expected_vars}, got {matrices['variables']}"
    print(f"  Pass Variables correctly ordered: {matrices['variables']}")
    
    # Objective should be minimize r (c = [0, 0, 0, 1])
    expected_c = [0.0, 0.0, 0.0, 1.0]
    assert matrices['c'] == expected_c, f"Expected objective {expected_c}, got {matrices['c']}"
    print(f"  Pass Objective correct: {matrices['c']}")
    
    # Should have 7 constraints (all inequalities)
    assert len(matrices['A_ub']) == 7, f"Expected 7 constraints, got {len(matrices['A_ub'])}"
    print(f"  Pass Correct number of constraints: {len(matrices['A_ub'])}")
    
    # Check bounds
    expected_bounds = [
        (6.66, 26.66),  # x1
        (4.0, 16.0),    # x2
        (1.25, 5.0),    # x3
        (0.0, 100.0)    # r
    ]
    assert matrices['bounds'] == expected_bounds, f"Expected bounds {expected_bounds}, got {matrices['bounds']}"
    print(f"  Pass Bounds correct: {matrices['bounds']}")
    
    print("\n" + "=" * 60)
    print("PASS: Complete paving problem pipeline works!")
    print("=" * 60)
    
    return True


def test_simple_problem():
    """Test a simple problem to verify basic functionality."""
    print("\n" + "=" * 60)
    print("Simple Problem Test")
    print("=" * 60)
    
    # Simple problem: maximize x + y subject to x <= 5, y <= 3, x + y <= 7
    # Convert to minimization: minimize -x - y
    constraint_expressions = [
        "x <= 5",
        "y <= 3",
        "x + y <= 7",
    ]
    
    dsl_expressions = [
        "DECISION(x)",
        "DECISION(y)",
        "OBJECTIVE(-x - y)",  # Maximize x + y = minimize -x - y
        "BOUND(x,0,None)",
        "BOUND(y,0,None)",
    ]
    
    # Extract constraints
    constraints = []
    for expr in constraint_expressions:
        constraints.extend(extract_constraints(expr))
    
    # Parse DSL
    all_decisions = []
    all_bounds = []
    all_objectives = []
    for expr in dsl_expressions:
        dsl_info = parse_dsl(expr)
        all_decisions.extend(dsl_info.decisions)
        all_bounds.extend(dsl_info.bounds)
        all_objectives.extend(dsl_info.objectives)
    
    dsl_info = DSLInfo(
        decisions=all_decisions,
        bounds=all_bounds,
        objectives=all_objectives
    )
    
    # Build matrices
    builder = MatrixBuilderV3()
    matrices = builder.build_matrices(constraints, dsl_info)
    
    print(f"Variables: {matrices['variables']}")
    print(f"Objective (c): {matrices['c']}")
    print(f"Constraints (A_ub):")
    for i, row in enumerate(matrices['A_ub']):
        print(f"  Row {i}: {row} <= {matrices['b_ub'][i]}")
    print(f"Bounds: {matrices['bounds']}")
    
    # Verify
    assert matrices['variables'] == ['x', 'y'], f"Expected ['x', 'y'], got {matrices['variables']}"
    assert matrices['c'] == [-1.0, -1.0], f"Expected [-1, -1], got {matrices['c']}"
    assert len(matrices['A_ub']) == 3, f"Expected 3 constraints, got {len(matrices['A_ub'])}"
    assert matrices['bounds'] == [(0.0, None), (0.0, None)], f"Expected [(0, None), (0, None)], got {matrices['bounds']}"
    
    print("\nPass Simple problem test passed!")
    return True


def test_equality_constraint():
    """Test equality constraint expansion."""
    print("\n" + "=" * 60)
    print("Equality Constraint Test")
    print("=" * 60)
    
    constraint_expressions = [
        "x + y == 10",
    ]
    
    dsl_expressions = [
        "DECISION(x)",
        "DECISION(y)",
        "OBJECTIVE(x + y)",
        "BOUND(x,0,None)",
        "BOUND(y,0,None)",
    ]
    
    # Extract constraints
    constraints = []
    for expr in constraint_expressions:
        constraints.extend(extract_constraints(expr))
    
    # Parse DSL
    all_decisions = []
    all_bounds = []
    all_objectives = []
    for expr in dsl_expressions:
        dsl_info = parse_dsl(expr)
        all_decisions.extend(dsl_info.decisions)
        all_bounds.extend(dsl_info.bounds)
        all_objectives.extend(dsl_info.objectives)
    
    dsl_info = DSLInfo(
        decisions=all_decisions,
        bounds=all_bounds,
        objectives=all_objectives
    )
    
    # Build matrices
    builder = MatrixBuilderV3()
    matrices = builder.build_matrices(constraints, dsl_info)
    
    print(f"Variables: {matrices['variables']}")
    print(f"Objective (c): {matrices['c']}")
    print(f"Constraints (A_ub):")
    for i, row in enumerate(matrices['A_ub']):
        print(f"  Row {i}: {row} <= {matrices['b_ub'][i]}")
    print(f"Bounds: {matrices['bounds']}")
    
    # Verify equality was expanded to two inequalities
    assert len(matrices['A_ub']) == 2, f"Expected 2 constraints (equality expansion), got {len(matrices['A_ub'])}"
    assert matrices['A_ub'][0] == [1.0, 1.0], f"Expected [1, 1], got {matrices['A_ub'][0]}"
    assert matrices['b_ub'][0] == 10.0, f"Expected 10.0, got {matrices['b_ub'][0]}"
    assert matrices['A_ub'][1] == [-1.0, -1.0], f"Expected [-1, -1], got {matrices['A_ub'][1]}"
    assert matrices['b_ub'][1] == -10.0, f"Expected -10.0, got {matrices['b_ub'][1]}"
    
    print("\nPass Equality constraint test passed!")
    return True


def main():
    """Run all integration tests."""
    print("Week-2 + Week-3 Integration Tests")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Simple Problem", test_simple_problem()))
    except Exception as e:
        print(f"Simple Problem test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Simple Problem", False))
    
    try:
        results.append(("Equality Constraint", test_equality_constraint()))
    except Exception as e:
        print(f"Equality Constraint test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Equality Constraint", False))
    
    try:
        results.append(("Paving Problem", test_paving_problem_complete()))
    except Exception as e:
        print(f"Paving Problem test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Paving Problem", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL INTEGRATION TESTS PASSED!")
        print("\nWeek-2 + Week-3 Pipeline Complete:")
        print("Pass DSL parsing and constraint extraction")
        print("Pass Canonical transformation")
        print("Pass Matrix building for solver")
        print("Pass Paving problem integration")
    else:
        print("SOME INTEGRATION TESTS FAILED")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)