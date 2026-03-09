#!/usr/bin/env python3
"""
Simple test script for AST Expression Parser (Week 1)
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ast_expression_parser import (
    parse_expression,
    evaluate_expression,
    extract_variables,
    simplify_expression,
    ASTExpressionParser,
    ExpressionEvaluator,
    VariableExtractor,
    ExpressionSimplifier,
    ConstantNode,
    VariableNode,
    BinaryOpNode,
    UnaryOpNode,
    Operator
)


def run_basic_tests():
    """Run basic tests for the AST parser."""
    print("AST Expression Parser - Week 1 Implementation Test")
    print("=" * 60)
    
    # Test 1: Basic parsing
    print("\n1. Basic Parsing Tests:")
    test_cases = [
        ("42", "Constant"),
        ("x", "Variable"),
        ("x + y", "BinaryOp"),
        ("-x", "UnaryOp"),
        ("(x + y)", "BinaryOp with parentheses"),
        ("2*x + 3*y", "Complex expression"),
    ]
    
    for expr, description in test_cases:
        try:
            node = parse_expression(expr)
            print(f"  [OK] {description}: '{expr}' -> {type(node).__name__}")
        except Exception as e:
            print(f"  [ERROR] {description}: '{expr}' -> ERROR: {e}")
    
    # Test 2: Evaluation
    print("\n2. Evaluation Tests:")
    context = {"x": 5.0, "y": 3.0, "z": 2.0}
    eval_cases = [
        ("x + y", 8.0),
        ("x - y", 2.0),
        ("x * y", 15.0),
        ("x / y", 5.0/3.0),
        ("(x + y) * z", 16.0),
        ("-x + y", -2.0),
    ]
    
    for expr, expected in eval_cases:
        try:
            result = evaluate_expression(expr, context)
            if abs(result - expected) < 1e-10:
                print(f"  Ok '{expr}' = {result} (expected: {expected})")
            else:
                print(f"  [ERROR] '{expr}' = {result} (expected: {expected})")
        except Exception as e:
            print(f"  [ERROR] '{expr}' -> ERROR: {e}")
    
    # Test 3: Variable extraction
    print("\n3. Variable Extraction Tests:")
    var_cases = [
        ("42", set()),
        ("x", {"x"}),
        ("x + y", {"x", "y"}),
        ("2*x + 3*y - 4", {"x", "y"}),
        ("(x + y) * (a - b)", {"x", "y", "a", "b"}),
        ("-x + y", {"x", "y"}),
    ]
    
    for expr, expected in var_cases:
        try:
            variables = extract_variables(expr)
            if variables == expected:
                print(f"  Ok '{expr}' -> {variables}")
            else:
                print(f"  [ERROR] '{expr}' -> {variables} (expected: {expected})")
        except Exception as e:
            print(f"  [ERROR] '{expr}' -> ERROR: {e}")
    
    # Test 4: Simplification
    print("\n4. Simplification Tests:")
    simpl_cases = [
        ("2 + 3", "5.0"),
        ("x + 0", "x"),
        ("0 + x", "x"),
        ("x - 0", "x"),
        ("x * 1", "x"),
        ("1 * x", "x"),
        ("x / 1", "x"),
        ("x * 0", "0.0"),
        ("0 * x", "0.0"),
        ("0 / x", "0.0"),
        ("0 - x", "(-x)"),
        ("-(-x)", "x"),
        ("-(5)", "-5.0"),
        ("(x)", "x"),
        ("((x))", "x"),
        ("2*x + 0*y - x", "x"),
    ]
    
    for expr, expected in simpl_cases:
        try:
            simplified = simplify_expression(expr)
            if simplified == expected:
                print(f"  Ok '{expr}' -> '{simplified}'")
            else:
                print(f"  [ERROR] '{expr}' -> '{simplified}' (expected: '{expected}')")
        except Exception as e:
            print(f"  [ERROR] '{expr}' -> ERROR: {e}")
    
    # Test 5: Error handling
    print("\n5. Error Handling Tests:")
    error_cases = [
        ("x +", "Invalid syntax"),
        ("x @ y", "Invalid operator"),
        ("x <= y", "Comparison not supported"),
        ("pow(x, 2)", "Function calls not fully supported"),
        ("", "Empty expression"),
    ]
    
    for expr, description in error_cases:
        try:
            result = evaluate_expression(expr, {})
            print(f"  [ERROR] '{expr}' -> {result} (should have failed: {description})")
        except Exception as e:
            print(f"  Ok '{expr}' -> ERROR as expected: {type(e).__name__}: {str(e)[:50]}...")
    
    print("\n" + "=" * 60)
    print("Week 1 AST Parser Implementation Test Complete")


def test_integration_with_existing():
    """Test integration with existing formula runtime patterns."""
    print("\n\nIntegration with Existing Formula Runtime")
    print("=" * 60)
    
    # Test expressions similar to those in existing system
    integration_cases = [
        ("P_J - C_J", {"P_J": 20.0, "C_J": 10.0}, 10.0),
        ("2*x1 + 3*x2", {"x1": 1.0, "x2": 2.0}, 8.0),
        ("CM_J", {"CM_J": [10, 6, 8]}, None),  # Will fail - lists not supported
    ]
    
    for expr, context, expected in integration_cases:
        try:
            result = evaluate_expression(expr, context)
            if expected is not None:
                if abs(result - expected) < 1e-10:
                    print(f"  Ok '{expr}' = {result} (matches existing system pattern)")
                else:
                    print(f"  [ERROR] '{expr}' = {result} (expected: {expected})")
            else:
                print(f"  Ok '{expr}' -> {result} (unexpected success)")
        except Exception as e:
            error_msg = str(e)
            if "function calls" in error_msg or "Function calls" in error_msg:
                print(f"  Ok '{expr}' -> ERROR as expected for Week 1: Function calls not supported")
            elif "list" in error_msg or "List" in error_msg:
                print(f"  Ok '{expr}' -> ERROR as expected: Lists not supported in linear expressions")
            else:
                print(f"  ? '{expr}' -> Unexpected error: {type(e).__name__}: {error_msg[:50]}...")


def run_ast_parser_directly():
    """Test the AST parser classes directly."""
    print("\n\nDirect AST Parser Class Tests")
    print("=" * 60)
    
    parser = ASTExpressionParser()
    
    # Test parsing
    expr = "2*x + 3*y - 4"
    print(f"\nParsing expression: '{expr}'")
    node = parser.parse(expr)
    print(f"  AST Node type: {type(node).__name__}")
    print(f"  String representation: {node}")
    
    # Test evaluation
    evaluator = ExpressionEvaluator({"x": 5.0, "y": 2.0})
    result = node.accept(evaluator)
    print(f"  Evaluation result: {result}")
    print(f"  Expected: {2*5 + 3*2 - 4}")
    
    # Test variable extraction
    extractor = VariableExtractor()
    variables = extractor.extract(node)
    print(f"  Extracted variables: {variables}")
    
    # Test simplification
    simplifier = ExpressionSimplifier()
    simplified_node = node.accept(simplifier)
    print(f"  Simplified: {simplified_node}")


if __name__ == "__main__":
    run_basic_tests()
    test_integration_with_existing()
    run_ast_parser_directly()