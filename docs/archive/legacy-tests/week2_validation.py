"""
Week-2 Production Validation

Perform comprehensive testing before Week-3 begins:
1. symbolic edge-case testing
2. vector consistency testing  
3. bound override testing
4. equality stability testing
5. full end-to-end DSL test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ast_expression_parser import parse_expression, extract_variables
from constraint_extractor import extract_constraints, Constraint
from dsl_parser import parse_dsl, detect_dsl, DSLDecision, DSLBound, DSLObjective
from unicode_normalizer import normalize_expression


def test_symbolic_edge_cases():
    """Test symbolic edge cases in constraint parsing."""
    print("=" * 70)
    print("1. SYMBOLIC EDGE-CASE TESTING")
    print("=" * 70)
    
    edge_cases = [
        # Basic edge cases
        ("0 <= 0", "0 <= 0"),
        ("x <= x", "x <= x"),
        ("-x <= x", "-x <= x"),
        ("x <= -x", "x <= -x"),
        
        # Complex expressions
        ("(x + y) * 2 <= 3 * (a - b)", "(x + y) * 2 <= 3 * (a - b)"),
        ("x/y <= z", "x/y <= z"),  # Division
        ("x**2 <= y", "x**2 <= y"),  # Power
        
        # Multiple comparisons (should fail - not supported)
        ("x <= y <= z", "x <= y <= z"),
        
        # Negative coefficients
        ("-2*x - 3*y <= -5", "-2*x - 3*y <= -5"),
        ("2*x - 3*y >= 5", "2*x - 3*y >= 5"),
        
        # Decimal and scientific notation
        ("1.5e-3*x <= 2.5", "1.5e-3*x <= 2.5"),
        ("0.001*x <= 0.002", "0.001*x <= 0.002"),
    ]
    
    results = []
    for expr, _ in edge_cases:
        try:
            # Try to parse
            ast_node = parse_expression(expr)
            
            # Try to extract constraints
            constraints = extract_constraints(expr)
            
            results.append({
                'expression': expr,
                'parsed': True,
                'constraints': len(constraints),
                'error': None
            })
            print(f"[OK] {expr}")
            print(f"  Parsed: Yes, Constraints: {len(constraints)}")
            for i, c in enumerate(constraints):
                print(f"    Constraint {i+1}: {c}")
                
        except Exception as e:
            results.append({
                'expression': expr,
                'parsed': False,
                'constraints': 0,
                'error': str(e)
            })
            print(f"[FAIL] {expr}")
            print(f"  Error: {e}")
    
    # Summary
    parsed_count = sum(1 for r in results if r['parsed'])
    print(f"\nSummary: {parsed_count}/{len(results)} edge cases parsed successfully")
    
    return results


def test_vector_consistency():
    """Test vector variable consistency in DECISION expansion."""
    print("\n" + "=" * 70)
    print("2. VECTOR CONSISTENCY TESTING")
    print("=" * 70)
    
    test_cases = [
        ("DECISION(x)", ["x"]),
        ("DECISION(x, size=1)", ["x"]),
        ("DECISION(x, size=3)", ["x1", "x2", "x3"]),
        ("DECISION(x, size=5)", ["x1", "x2", "x3", "x4", "x5"]),
        ("DECISION(var123, size=2)", ["var1231", "var1232"]),
    ]
    
    results = []
    for expr, expected_vars in test_cases:
        try:
            dsl_info = parse_dsl(expr)
            
            if len(dsl_info.decisions) != 1:
                raise ValueError(f"Expected 1 decision, got {len(dsl_info.decisions)}")
            
            decision = dsl_info.decisions[0]
            actual_vars = decision.vector_variables
            
            passed = actual_vars == expected_vars
            results.append({
                'expression': expr,
                'expected': expected_vars,
                'actual': actual_vars,
                'passed': passed,
                'error': None
            })
            
            status = "[OK]" if passed else "[FAIL]"
            print(f"{status} {expr}")
            print(f"  Expected: {expected_vars}")
            print(f"  Actual: {actual_vars}")
            
        except Exception as e:
            results.append({
                'expression': expr,
                'expected': expected_vars,
                'actual': None,
                'passed': False,
                'error': str(e)
            })
            print(f"[FAIL] {expr}")
            print(f"  Error: {e}")
    
    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    print(f"\nSummary: {passed_count}/{len(results)} vector tests passed")
    
    return results


def test_bound_override():
    """Test BOUND function parsing and validation."""
    print("\n" + "=" * 70)
    print("3. BOUND OVERRIDE TESTING")
    print("=" * 70)
    
    test_cases = [
        # Basic bounds
        ("BOUND(x, 0, 10)", ("x", 0.0, 10.0)),
        ("BOUND(y, -5, 5)", ("y", -5.0, 5.0)),
        ("BOUND(z, 1.5, 2.5)", ("z", 1.5, 2.5)),
        
        # Negative bounds
        ("BOUND(a, -10, -1)", ("a", -10.0, -1.0)),
        
        # Zero bounds
        ("BOUND(b, 0, 0)", ("b", 0.0, 0.0)),
        
        # Large bounds
        ("BOUND(c, -1000, 1000)", ("c", -1000.0, 1000.0)),
    ]
    
    results = []
    for expr, (expected_var, expected_lower, expected_upper) in test_cases:
        try:
            dsl_info = parse_dsl(expr)
            
            if len(dsl_info.bounds) != 1:
                raise ValueError(f"Expected 1 bound, got {len(dsl_info.bounds)}")
            
            bound = dsl_info.bounds[0]
            
            passed = (bound.variable_name == expected_var and
                     abs(bound.lower - expected_lower) < 1e-10 and
                     abs(bound.upper - expected_upper) < 1e-10)
            
            results.append({
                'expression': expr,
                'expected': (expected_var, expected_lower, expected_upper),
                'actual': (bound.variable_name, bound.lower, bound.upper),
                'passed': passed,
                'error': None
            })
            
            status = "[OK]" if passed else "[FAIL]"
            print(f"{status} {expr}")
            print(f"  Expected: {expected_var}, [{expected_lower}, {expected_upper}]")
            print(f"  Actual: {bound.variable_name}, [{bound.lower}, {bound.upper}]")
            
        except Exception as e:
            results.append({
                'expression': expr,
                'expected': (expected_var, expected_lower, expected_upper),
                'actual': None,
                'passed': False,
                'error': str(e)
            })
            print(f"[FAIL] {expr}")
            print(f"  Error: {e}")
    
    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    print(f"\nSummary: {passed_count}/{len(results)} bound tests passed")
    
    return results


def test_equality_stability():
    """Test equality constraint stability and correctness."""
    print("\n" + "=" * 70)
    print("4. EQUALITY STABILITY TESTING")
    print("=" * 70)
    
    test_cases = [
        ("x == y", 2, ["x - y <= 0", "-x + y <= 0"]),
        ("2*x == 3*y", 2, ["2*x - 3*y <= 0", "-2*x + 3*y <= 0"]),
        ("x + y == 5", 2, ["x + y <= 5", "-x - y <= -5"]),
        ("x == 0", 2, ["x <= 0", "-x <= 0"]),
        ("0 == x", 2, ["-x <= 0", "x <= 0"]),
        ("a + b == c + d", 2, ["a + b - c - d <= 0", "-a - b + c + d <= 0"]),
    ]
    
    results = []
    for expr, expected_count, expected_patterns in test_cases:
        try:
            constraints = extract_constraints(expr)
            
            passed = len(constraints) == expected_count
            
            # Check constraint patterns (handle -0.0 vs 0 and 2.0 vs 2 floating point issues)
            constraint_strs = [str(c) for c in constraints]
            # Normalize -0.0 to 0 and 2.0 to 2 for comparison
            normalized_strs = []
            for s in constraint_strs:
                # Replace -0.0 with 0
                s = s.replace('<= -0.0', '<= 0')
                # Replace .0 with empty string (2.0 -> 2)
                s = s.replace('.0*', '*').replace('.0 ', ' ')
                normalized_strs.append(s)
            
            # Also normalize expected patterns
            normalized_patterns = []
            for pattern in expected_patterns:
                pattern = pattern.replace('.0*', '*').replace('.0 ', ' ')
                normalized_patterns.append(pattern)
            
            pattern_matches = all(
                any(pattern in constr for constr in normalized_strs)
                for pattern in normalized_patterns
            )
            
            results.append({
                'expression': expr,
                'expected_count': expected_count,
                'actual_count': len(constraints),
                'constraints': constraint_strs,
                'passed': passed and pattern_matches,
                'error': None
            })
            
            status = "[OK]" if passed and pattern_matches else "[FAIL]"
            print(f"{status} {expr}")
            print(f"  Expected: {expected_count} constraints")
            print(f"  Actual: {len(constraints)} constraints")
            for i, constr in enumerate(constraint_strs):
                print(f"    Constraint {i+1}: {constr}")
            
        except Exception as e:
            results.append({
                'expression': expr,
                'expected_count': expected_count,
                'actual_count': 0,
                'constraints': [],
                'passed': False,
                'error': str(e)
            })
            print(f"[FAIL] {expr}")
            print(f"  Error: {e}")
    
    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    print(f"\nSummary: {passed_count}/{len(results)} equality tests passed")
    
    return results


def test_end_to_end_dsl():
    """Test full end-to-end DSL workflow."""
    print("\n" + "=" * 70)
    print("5. END-TO-END DSL TEST")
    print("=" * 70)
    
    # Complete DSL problem
    dsl_problem = """
    DECISION(x, size=3)
    DECISION(y)
    BOUND(x1, 0, 10)
    BOUND(x2, 5, 15)
    BOUND(x3, -5, 5)
    BOUND(y, 0, 100)
    OBJECTIVE(2*x1 + 3*x2 - x3 + y)
    x1 + x2 <= 20
    x3 >= 0
    y == 2*x1 + x2
    """
    
    # Split into individual expressions (since "AND" not supported)
    expressions = [
        "DECISION(x, size=3)",
        "DECISION(y)",
        "BOUND(x1, 0, 10)",
        "BOUND(x2, 5, 15)",
        "BOUND(x3, -5, 5)",
        "BOUND(y, 0, 100)",
        "OBJECTIVE(2*x1 + 3*x2 - x3 + y)",
        "x1 + x2 <= 20",
        "x3 >= 0",
        "y == 2*x1 + x2",
    ]
    
    print("Testing complete DSL problem:")
    print("-" * 40)
    
    results = []
    all_decisions = []
    all_bounds = []
    all_objectives = []
    all_constraints = []
    
    for expr in expressions:
        try:
            # Check if it's a DSL function
            if any(keyword in expr.upper() for keyword in ['DECISION', 'BOUND', 'OBJECTIVE']):
                dsl_info = parse_dsl(expr)
                all_decisions.extend(dsl_info.decisions)
                all_bounds.extend(dsl_info.bounds)
                all_objectives.extend(dsl_info.objectives)
                print(f"[OK] DSL: {expr}")
            else:
                # It's a constraint
                constraints = extract_constraints(expr)
                all_constraints.extend(constraints)
                print(f"[OK] Constraint: {expr}")
                for c in constraints:
                    print(f"    -> {c}")
                
            results.append({
                'expression': expr,
                'passed': True,
                'error': None
            })
            
        except Exception as e:
            results.append({
                'expression': expr,
                'passed': False,
                'error': str(e)
            })
            print(f"[FAIL] {expr}")
            print(f"  Error: {e}")
    
    # Summary
    print("\n" + "-" * 40)
    print("DSL Problem Summary:")
    print(f"  Decisions: {len(all_decisions)}")
    for d in all_decisions:
        print(f"    - {d}")
    
    print(f"  Bounds: {len(all_bounds)}")
    for b in all_bounds:
        print(f"    - {b}")
    
    print(f"  Objectives: {len(all_objectives)}")
    for o in all_objectives:
        print(f"    - {o}")
    
    print(f"  Constraints: {len(all_constraints)}")
    for c in all_constraints:
        print(f"    - {c}")
    
    passed_count = sum(1 for r in results if r['passed'])
    print(f"\nEnd-to-end test: {passed_count}/{len(results)} expressions processed")
    
    return results


def main():
    """Run all validation tests."""
    print("WEEK-2 PRODUCTION VALIDATION")
    print("=" * 70)
    
    # Run all tests
    edge_results = test_symbolic_edge_cases()
    vector_results = test_vector_consistency()
    bound_results = test_bound_override()
    equality_results = test_equality_stability()
    e2e_results = test_end_to_end_dsl()
    
    # Overall summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    all_results = edge_results + vector_results + bound_results + equality_results
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.get('passed', False))
    
    print(f"Total tests: {total_tests}")
    print(f"Passed tests: {passed_tests}")
    print(f"Failed tests: {total_tests - passed_tests}")
    
    # Identify failing cases
    failing_cases = []
    for results in [edge_results, vector_results, bound_results, equality_results]:
        for r in results:
            if not r.get('passed', False):
                failing_cases.append({
                    'expression': r['expression'],
                    'error': r.get('error', 'Unknown error')
                })
    
    if failing_cases:
        print("\nFAILING CASES:")
        for i, case in enumerate(failing_cases, 1):
            print(f"{i}. {case['expression']}")
            print(f"   Error: {case['error']}")
    
    # Readiness verdict
    print("\n" + "=" * 70)
    print("READINESS VERDICT")
    print("=" * 70)
    
    if passed_tests == total_tests:
        print("[PASS] WEEK-2 IMPLEMENTATION IS PRODUCTION READY")
        print("All validation tests passed successfully.")
        print("The system is ready for Week-3 matrix integration.")
    else:
        print("[WARNING] WEEK-2 IMPLEMENTATION NEEDS FIXES")
        print(f"{total_tests - passed_tests} tests failed.")
        print("See failing cases above for required fixes.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)