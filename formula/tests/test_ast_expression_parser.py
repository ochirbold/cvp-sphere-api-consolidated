"""
Unit tests for AST Expression Parser (Week 1)

This module tests the Week 1 deliverables:
1. AST node hierarchy for LP expressions
2. Minimal parser for linear expressions only (+, -, *, /, parentheses)
3. Support for linear expressions only
4. Unit tests for expression parsing

Test Categories:
- Basic parsing and evaluation
- Variable extraction
- Expression simplification
- Error handling
- Integration with existing system
"""

import sys
import os
import unittest
import math

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    Operator,
    NodeType
)


class TestASTExpressionParser(unittest.TestCase):
    """Test the AST expression parser functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ASTExpressionParser()
    
    def test_parse_constant(self):
        """Test parsing constant expressions."""
        # Test integer constant
        node = self.parser.parse("42")
        self.assertIsInstance(node, ConstantNode)
        self.assertEqual(node.value, 42.0)
        
        # Test float constant
        node = self.parser.parse("3.14")
        self.assertIsInstance(node, ConstantNode)
        self.assertEqual(node.value, 3.14)
        
        # Test negative constant
        node = self.parser.parse("-5")
        self.assertIsInstance(node, UnaryOpNode)
        self.assertEqual(node.operator, Operator.NEGATE)
        self.assertIsInstance(node.operand, ConstantNode)
        self.assertEqual(node.operand.value, 5.0)
    
    def test_parse_variable(self):
        """Test parsing variable expressions."""
        # Test single variable
        node = self.parser.parse("x")
        self.assertIsInstance(node, VariableNode)
        self.assertEqual(node.name, "x")
        
        # Test variable with number
        node = self.parser.parse("x1")
        self.assertIsInstance(node, VariableNode)
        self.assertEqual(node.name, "x1")
        
        # Test multiple variables
        node = self.parser.parse("profit_margin")
        self.assertIsInstance(node, VariableNode)
        self.assertEqual(node.name, "profit_margin")
    
    def test_parse_binary_operations(self):
        """Test parsing binary operations."""
        # Test addition
        node = self.parser.parse("x + y")
        self.assertIsInstance(node, BinaryOpNode)
        self.assertEqual(node.operator, Operator.ADD)
        self.assertIsInstance(node.left, VariableNode)
        self.assertIsInstance(node.right, VariableNode)
        
        # Test subtraction
        node = self.parser.parse("x - y")
        self.assertEqual(node.operator, Operator.SUBTRACT)
        
        # Test multiplication
        node = self.parser.parse("x * y")
        self.assertEqual(node.operator, Operator.MULTIPLY)
        
        # Test division
        node = self.parser.parse("x / y")
        self.assertEqual(node.operator, Operator.DIVIDE)
        
        # Test complex expression
        node = self.parser.parse("2*x + 3*y")
        self.assertEqual(node.operator, Operator.ADD)
        self.assertIsInstance(node.left, BinaryOpNode)
        self.assertIsInstance(node.right, BinaryOpNode)
    
    def test_parse_parentheses(self):
        """Test parsing expressions with parentheses."""
        # Test simple parentheses
        node = self.parser.parse("(x + y)")
        self.assertIsInstance(node, BinaryOpNode)  # Parentheses are implicit in AST structure
        
        # Test nested parentheses
        node = self.parser.parse("(x + (y * z))")
        self.assertEqual(node.operator, Operator.ADD)
        
        # Test parentheses with multiplication
        node = self.parser.parse("(x + y) * z")
        self.assertEqual(node.operator, Operator.MULTIPLY)
    
    def test_parse_unary_operations(self):
        """Test parsing unary operations."""
        # Test unary minus
        node = self.parser.parse("-x")
        self.assertIsInstance(node, UnaryOpNode)
        self.assertEqual(node.operator, Operator.NEGATE)
        self.assertIsInstance(node.operand, VariableNode)
        
        # Test complex unary expression
        node = self.parser.parse("-(x + y)")
        self.assertIsInstance(node, UnaryOpNode)
        self.assertIsInstance(node.operand, BinaryOpNode)
    
    def test_parse_errors(self):
        """Test parsing error cases."""
        # Test invalid syntax
        with self.assertRaises(SyntaxError):
            self.parser.parse("x +")
        
        # Test invalid characters
        with self.assertRaises(ValueError):
            self.parser.parse("x @ y")
        
        # Test comparison expressions (not supported in Week 1)
        with self.assertRaises(ValueError):
            self.parser.parse("x <= y")
        
        # Test function calls (not fully supported in Week 1)
        with self.assertRaises(ValueError):
            self.parser.parse("pow(x, 2)")


class TestExpressionEvaluator(unittest.TestCase):
    """Test expression evaluation functionality."""
    
    def test_evaluate_constant(self):
        """Test evaluating constant expressions."""
        evaluator = ExpressionEvaluator({})
        
        # Test integer constant
        node = ConstantNode(42.0)
        result = evaluator.visit_constant(node)
        self.assertEqual(result, 42.0)
        
        # Test float constant
        node = ConstantNode(3.14)
        result = evaluator.visit_constant(node)
        self.assertEqual(result, 3.14)
    
    def test_evaluate_variable(self):
        """Test evaluating variable expressions."""
        context = {"x": 5.0, "y": 3.0}
        evaluator = ExpressionEvaluator(context)
        
        # Test single variable
        node = VariableNode("x")
        result = evaluator.visit_variable(node)
        self.assertEqual(result, 5.0)
        
        # Test missing variable
        node = VariableNode("z")
        with self.assertRaises(KeyError):
            evaluator.visit_variable(node)
    
    def test_evaluate_binary_operations(self):
        """Test evaluating binary operations."""
        context = {"x": 4.0, "y": 2.0}
        evaluator = ExpressionEvaluator(context)
        
        # Test addition
        node = BinaryOpNode(Operator.ADD, VariableNode("x"), VariableNode("y"))
        result = evaluator.visit_binary_op(node)
        self.assertEqual(result, 6.0)
        
        # Test subtraction
        node = BinaryOpNode(Operator.SUBTRACT, VariableNode("x"), VariableNode("y"))
        result = evaluator.visit_binary_op(node)
        self.assertEqual(result, 2.0)
        
        # Test multiplication
        node = BinaryOpNode(Operator.MULTIPLY, VariableNode("x"), VariableNode("y"))
        result = evaluator.visit_binary_op(node)
        self.assertEqual(result, 8.0)
        
        # Test division
        node = BinaryOpNode(Operator.DIVIDE, VariableNode("x"), VariableNode("y"))
        result = evaluator.visit_binary_op(node)
        self.assertEqual(result, 2.0)
        
        # Test division by zero
        node = BinaryOpNode(Operator.DIVIDE, VariableNode("x"), ConstantNode(0.0))
        with self.assertRaises(ZeroDivisionError):
            evaluator.visit_binary_op(node)
    
    def test_evaluate_unary_operations(self):
        """Test evaluating unary operations."""
        context = {"x": 5.0}
        evaluator = ExpressionEvaluator(context)
        
        # Test unary minus
        node = UnaryOpNode(Operator.NEGATE, VariableNode("x"))
        result = evaluator.visit_unary_op(node)
        self.assertEqual(result, -5.0)
        
        # Test double negation
        inner = UnaryOpNode(Operator.NEGATE, VariableNode("x"))
        node = UnaryOpNode(Operator.NEGATE, inner)
        result = evaluator.visit_unary_op(node)
        self.assertEqual(result, 5.0)
    
    def test_evaluate_complex_expressions(self):
        """Test evaluating complex expressions."""
        context = {"x": 3.0, "y": 4.0, "z": 2.0}
        
        # Test (x + y) * z
        result = evaluate_expression("(x + y) * z", context)
        self.assertEqual(result, (3 + 4) * 2)
        
        # Test x * y - z / 2
        result = evaluate_expression("x * y - z / 2", context)
        self.assertEqual(result, (3 * 4) - (2 / 2))
        
        # Test -x + y * 3
        result = evaluate_expression("-x + y * 3", context)
        self.assertEqual(result, -3 + (4 * 3))


class TestVariableExtractor(unittest.TestCase):
    """Test variable extraction functionality."""
    
    def test_extract_variables_simple(self):
        """Test extracting variables from simple expressions."""
        # Test constant
        variables = extract_variables("42")
        self.assertEqual(variables, set())
        
        # Test single variable
        variables = extract_variables("x")
        self.assertEqual(variables, {"x"})
        
        # Test multiple variables
        variables = extract_variables("x + y")
        self.assertEqual(variables, {"x", "y"})
    
    def test_extract_variables_complex(self):
        """Test extracting variables from complex expressions."""
        # Test expression with repeated variables
        variables = extract_variables("x * x + y - x")
        self.assertEqual(variables, {"x", "y"})
        
        # Test expression with constants and variables
        variables = extract_variables("2*x + 3*y - 4")
        self.assertEqual(variables, {"x", "y"})
        
        # Test nested expression
        variables = extract_variables("(x + y) * (a - b)")
        self.assertEqual(variables, {"x", "y", "a", "b"})
        
        # Test expression with unary operations
        variables = extract_variables("-x + y")
        self.assertEqual(variables, {"x", "y"})
    
    def test_extract_variables_edge_cases(self):
        """Test edge cases for variable extraction."""
        # Test empty expression (should fail parsing)
        with self.assertRaises(ValueError):
            extract_variables("")
        
        # Test expression with only operators (should fail parsing)
        with self.assertRaises(SyntaxError):
            extract_variables("+ - *")


class TestExpressionSimplifier(unittest.TestCase):
    """Test expression simplification functionality."""
    
    def test_simplify_constant_folding(self):
        """Test constant folding simplifications."""
        # Test simple addition
        simplified = simplify_expression("2 + 3")
        self.assertEqual(simplified, "5.0")
        
        # Test multiplication
        simplified = simplify_expression("2 * 3")
        self.assertEqual(simplified, "6.0")
        
        # Test complex constant expression
        simplified = simplify_expression("(2 + 3) * 4")
        self.assertEqual(simplified, "20.0")
        
        # Test division
        simplified = simplify_expression("10 / 2")
        self.assertEqual(simplified, "5.0")
    
    def test_simplify_identity_rules(self):
        """Test identity rule simplifications."""
        # Test x + 0 → x
        simplified = simplify_expression("x + 0")
        self.assertEqual(simplified, "x")
        
        # Test 0 + x → x
        simplified = simplify_expression("0 + x")
        self.assertEqual(simplified, "x")
        
        # Test x - 0 → x
        simplified = simplify_expression("x - 0")
        self.assertEqual(simplified, "x")
        
        # Test x * 1 → x
        simplified = simplify_expression("x * 1")
        self.assertEqual(simplified, "x")
        
        # Test 1 * x → x
        simplified = simplify_expression("1 * x")
        self.assertEqual(simplified, "x")
        
        # Test x / 1 → x
        simplified = simplify_expression("x / 1")
        self.assertEqual(simplified, "x")
    
    def test_simplify_zero_rules(self):
        """Test zero rule simplifications."""
        # Test x * 0 → 0
        simplified = simplify_expression("x * 0")
        self.assertEqual(simplified, "0.0")
        
        # Test 0 * x → 0
        simplified = simplify_expression("0 * x")
        self.assertEqual(simplified, "0.0")
        
        # Test 0 / x → 0
        simplified = simplify_expression("0 / x")
        self.assertEqual(simplified, "0.0")
        
        # Test 0 - x → -x
        simplified = simplify_expression("0 - x")
        self.assertEqual(simplified, "(-x)")
    
    def test_simplify_unary_operations(self):
        """Test unary operation simplifications."""
        # Test -(-x) → x
        simplified = simplify_expression("-(-x)")
        self.assertEqual(simplified, "x")
        
        # Test -(5) → -5
        simplified = simplify_expression("-(5)")
        self.assertEqual(simplified, "-5.0")
        
        # Test -(-(x + y)) → x + y
        simplified = simplify_expression("-(-(x + y))")
        self.assertEqual(simplified, "(x + y)")
    
    def test_simplify_parentheses(self):
        """Test parentheses simplification."""
        # Test (x) → x
        simplified = simplify_expression("(x)")
        self.assertEqual(simplified, "x")
        
        # Test ((x)) → x
        simplified = simplify_expression("((x))")
        self.assertEqual(simplified, "x")
        
        # Test (x + y) → (x + y) (parentheses preserved for binary ops)
        simplified = simplify_expression("(x + y)")
        self.assertEqual(simplified, "(x + y)")
        
        # Test (-x) → -x
        simplified = simplify_expression("(-x)")
        self.assertEqual(simplified, "(-x)")
    
    def test_simplify_complex_expressions(self):
        """Test simplification of complex expressions."""
        # Test 2*x + 0*y - x
        simplified = simplify_expression("2*x + 0*y - x")
        self.assertEqual(simplified, "x")
        
        # Test (x + 0) * 1 - (0 / y)
        simplified = simplify_expression("(x + 0) * 1 - (0 / y)")
        self.assertEqual(simplified, "x")
        
        # Test 3*(2 + 0) - 6
        simplified = simplify_expression("3*(2 + 0) - 6")
        self.assertEqual(simplified, "0.0")


class TestIntegration(unittest.TestCase):
    """Test integration with existing formula runtime patterns."""
    
    def test_public_api_functions(self):
        """Test the public API functions."""
        context = {"x": 5.0, "y": 3.0}
        
        # Test parse_expression
        node = parse_expression("x + y")
        self.assertIsInstance(node, BinaryOpNode)
        
        # Test evaluate_expression
        result = evaluate_expression("x + y", context)
        self.assertEqual(result, 8.0)
        
        # Test extract_variables
        variables = extract_variables("2*x + 3*y - 4")
        self.assertEqual(variables, {"x", "y"})
        
        # Test simplify_expression
        simplified = simplify_expression("x + 0")
        self.assertEqual(simplified, "x")
    
    def test_formula_runtime_compatibility(self):
        """Test compatibility with formula runtime patterns."""
        # Test expressions similar to those in formula_runtime.py
        test_cases = [
            ("P_J - C_J", {"P_J": 20.0, "C_J": 10.0}, 10.0),
            ("2*x1 + 3*x2", {"x1": 1.0, "x2": 2.0}, 8.0),
            ("-DOT(vector(CM_J),x)+NORM(vector(CM_J))*r", {}, None),  # Will fail - function calls
        ]
        
        for expr, context, expected in test_cases:
            try:
                result = evaluate_expression(expr, context)
                if expected is not None:
                    self.assertEqual(result, expected)
            except ValueError as e:
                # Function calls not supported in Week 1 - this is expected
                if "function calls" in str(e) or "Function calls" in str(e):
                    continue  # Expected error for Week 1
                raise
    
    def test_html_entity_decoding(self):
        """Test HTML entity decoding (for compatibility with existing system)."""
        # Test expression with HTML entities
        # Note: The parser should handle HTML entities like < for <
        # but comparison operators aren't supported in Week 1
        with self.assertRaises(ValueError):
            evaluate_expression("x <= y", {"x": 1.0, "y": 2.0})


class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def test_parse_performance(self):
        """Test parsing performance for typical expressions."""
        expressions = [
            "x + y",
            "2*x + 3*y - 4",
            "(x + y) * (a - b) / 2",
            "-x + y * 3 - z / 2",
        ]
        
        for expr in expressions:
            # Just ensure no exceptions
            node = parse_expression(expr)
            self.assertIsNotNone(node)
    
