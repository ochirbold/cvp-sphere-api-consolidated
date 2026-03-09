"""
Constraint Extractor for LP DSL Engine

This module extracts constraints from AST and transforms them to canonical LP form.

Week 2 Requirements:
1. Extract constraints from comparison expressions via AST
2. Transform to canonical LP form: a·x ≤ b
3. Support canonical rules:
   - a ≤ b → a - b ≤ 0
   - a ≥ b → -a + b ≤ 0
   - a = b → two constraints: a - b ≤ 0 AND -a + b ≤ 0

Design Principles:
- AST-based parsing only (no regex)
- Separation of concerns: extraction vs transformation
- Maintain backward compatibility
- Integration with existing AST parser
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
try:
    from formula.ast.parser import (
        ExpressionNode, ComparisonNode, BinaryOpNode, UnaryOpNode,
        ConstantNode, VariableNode, FunctionCallNode, ParenthesesNode,
        Operator, ExpressionVisitor
    )
except ImportError:
    from ..ast.parser import (
        ExpressionNode, ComparisonNode, BinaryOpNode, UnaryOpNode,
        ConstantNode, VariableNode, FunctionCallNode, ParenthesesNode,
        Operator, ExpressionVisitor
    )


@dataclass
class Constraint:
    """
    Canonical LP constraint: a·x ≤ b
    
    Represents a linear constraint in canonical form:
    Σ(coefficient_i * variable_i) ≤ constant
    
    For equality constraints (==), two constraints are created:
    1. Σ(coefficient_i * variable_i) ≤ constant
    2. -Σ(coefficient_i * variable_i) ≤ -constant
    """
    coefficients: Dict[str, float]  # variable -> coefficient
    constant: float                 # right-hand side constant
    sense: str                     # '<=', '>=', '=='
    original_expr: str             # Original expression for debugging
    
    def __str__(self) -> str:
        """String representation of constraint."""
        terms = []
        for var, coeff in sorted(self.coefficients.items()):
            if coeff == 1.0:
                terms.append(var)
            elif coeff == -1.0:
                terms.append(f"-{var}")
            else:
                terms.append(f"{coeff}*{var}")
        
        if not terms:
            expr = "0"
        else:
            expr = " + ".join(terms).replace("+ -", "- ")
        
        return f"{expr} {self.sense} {self.constant}"
    
    @classmethod
    def from_expression(cls, expr: ExpressionNode, sense: str, constant: float) -> 'Constraint':
        """
        Create constraint from expression in canonical form.
        
        Args:
            expr: Expression in canonical form (left side)
            sense: Constraint sense ('<=', '>=', '==')
            constant: Right-hand side constant (unused - we extract from expr)
            
        Returns:
            Constraint object
        """
        coefficient_extractor = CoefficientExtractor()
        coefficient_extractor.extract(expr)
        # The extractor collects both coefficients and constant term
        # The constant term is part of the expression (e.g., -5 in 2*x + 3*y - 5)
        # To get canonical form a·x ≤ b, we need to move constant to RHS
        # So if expression has constant term C, then RHS constant = -C
        coefficients = coefficient_extractor.coefficients
        rhs_constant = -coefficient_extractor.constant
        return cls(coefficients, rhs_constant, sense, str(expr))


class CoefficientExtractor(ExpressionVisitor):
    """
    Extracts variable coefficients from an expression.
    
    Assumes expression is in canonical form: Σ(coefficient_i * variable_i)
    """
    
    def __init__(self):
        self.coefficients: Dict[str, float] = {}
        self.constant: float = 0.0
    
    def visit_constant(self, node: ConstantNode) -> None:
        """Constant contributes to the constant term."""
        self.constant += node.value
    
    def visit_variable(self, node: VariableNode) -> None:
        """Variable with coefficient 1."""
        self.coefficients[node.name] = self.coefficients.get(node.name, 0.0) + 1.0
    
    def visit_binary_op(self, node: BinaryOpNode) -> None:
        """Handle binary operations."""
        if node.operator == Operator.ADD:
            # a + b: visit both sides
            node.left.accept(self)
            node.right.accept(self)
        elif node.operator == Operator.SUBTRACT:
            # a - b: visit left, then negative of right
            node.left.accept(self)
            # Create a unary negation for the right side
            neg_right = UnaryOpNode(Operator.NEGATE, node.right)
            neg_right.accept(self)
        elif node.operator == Operator.MULTIPLY:
            # a * b: handle coefficient * variable
            if isinstance(node.left, ConstantNode) and isinstance(node.right, VariableNode):
                # constant * variable
                self.coefficients[node.right.name] = self.coefficients.get(node.right.name, 0.0) + node.left.value
            elif isinstance(node.right, ConstantNode) and isinstance(node.left, VariableNode):
                # variable * constant
                self.coefficients[node.left.name] = self.coefficients.get(node.left.name, 0.0) + node.right.value
            else:
                raise ValueError(f"Unsupported multiplication in canonical form: {node}")
        else:
            raise ValueError(f"Unsupported operator in canonical form: {node.operator}")
    
    def visit_unary_op(self, node: UnaryOpNode) -> None:
        """Handle unary operations (negation)."""
        if node.operator == Operator.NEGATE:
            # -x: create a temporary visitor to extract and negate
            temp_extractor = CoefficientExtractor()
            node.operand.accept(temp_extractor)
            
            # Negate all coefficients and constant
            for var, coeff in temp_extractor.coefficients.items():
                self.coefficients[var] = self.coefficients.get(var, 0.0) - coeff
            self.constant -= temp_extractor.constant
        else:
            raise ValueError(f"Unsupported unary operator: {node.operator}")
    
    def visit_function_call(self, node: FunctionCallNode) -> None:
        """Function calls not supported in canonical form."""
        raise ValueError(f"Function calls not supported in canonical form: {node.function_name}")
    
    def visit_parentheses(self, node: ParenthesesNode) -> None:
        """Visit expression inside parentheses."""
        node.expression.accept(self)
    
    def visit_comparison(self, node: ComparisonNode) -> None:
        """Comparisons not expected in canonical form."""
        raise ValueError(f"Comparisons not expected in canonical form: {node}")
    
    def extract(self, node: ExpressionNode) -> Dict[str, float]:
        """
        Extract coefficients from expression.
        
        Args:
            node: Expression node in canonical form
            
        Returns:
            Dictionary mapping variable names to coefficients
        """
        self.coefficients.clear()
        self.constant = 0.0
        node.accept(self)
        
        # Move constant to RHS (it will be handled separately)
        # For now, just return coefficients
        return self.coefficients.copy()


class ConstraintExtractor(ExpressionVisitor):
    """
    Extracts constraints from AST and transforms to canonical form.
    """
    
    def __init__(self):
        self.constraints: List[Constraint] = []
    
    def visit_constant(self, node: ConstantNode) -> None:
        """Constants don't contain constraints."""
        pass
    
    def visit_variable(self, node: VariableNode) -> None:
        """Variables don't contain constraints."""
        pass
    
    def visit_binary_op(self, node: BinaryOpNode) -> None:
        """Visit both sides of binary operation."""
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_unary_op(self, node: UnaryOpNode) -> None:
        """Visit operand of unary operation."""
        node.operand.accept(self)
    
    def visit_function_call(self, node: FunctionCallNode) -> None:
        """Visit all arguments of function call."""
        for arg in node.arguments:
            arg.accept(self)
    
    def visit_parentheses(self, node: ParenthesesNode) -> None:
        """Visit expression inside parentheses."""
        node.expression.accept(self)
    
    def visit_comparison(self, node: ComparisonNode) -> None:
        """Extract constraint from comparison node."""
        constraints = self._extract_from_comparison(node)
        self.constraints.extend(constraints)
    
    def _extract_from_comparison(self, node: ComparisonNode) -> List[Constraint]:
        """
        Extract constraints from comparison node.
        
        Args:
            node: Comparison node
            
        Returns:
            List of constraints in canonical form
        """
        if node.operator == Operator.LE:
            # a ≤ b → a - b ≤ 0
            left_minus_right = BinaryOpNode(
                Operator.SUBTRACT,
                node.left,
                node.right
            )
            return [Constraint.from_expression(left_minus_right, '<=', 0.0)]
        
        elif node.operator == Operator.GE:
            # a ≥ b → -a + b ≤ 0
            neg_left = UnaryOpNode(Operator.NEGATE, node.left)
            neg_left_plus_right = BinaryOpNode(
                Operator.ADD,
                neg_left,
                node.right
            )
            return [Constraint.from_expression(neg_left_plus_right, '<=', 0.0)]
        
        elif node.operator == Operator.EQ:
            # a = b → a - b ≤ 0 AND -a + b ≤ 0
            left_minus_right = BinaryOpNode(
                Operator.SUBTRACT,
                node.left,
                node.right
            )
            neg_left = UnaryOpNode(Operator.NEGATE, node.left)
            neg_left_plus_right = BinaryOpNode(
                Operator.ADD,
                neg_left,
                node.right
            )
            return [
                Constraint.from_expression(left_minus_right, '<=', 0.0),
                Constraint.from_expression(neg_left_plus_right, '<=', 0.0)
            ]
        
        else:
            raise ValueError(f"Unsupported comparison operator: {node.operator}")
    
    def extract(self, node: ExpressionNode) -> List[Constraint]:
        """
        Extract all constraints from AST.
        
        Args:
            node: Root node of AST
            
        Returns:
            List of constraints in canonical form
        """
        self.constraints.clear()
        node.accept(self)
        return self.constraints.copy()


def extract_constraints(expression: str) -> List[Constraint]:
    """
    Extract constraints from expression string.
    
    Args:
        expression: String containing mathematical expression
        
    Returns:
        List of constraints in canonical form
        
    Raises:
        ValueError: If expression cannot be parsed
    """
    try:
        from .ast_expression_parser import parse_expression
    except ImportError:
        from ast_expression_parser import parse_expression
    ast_node = parse_expression(expression)
    extractor = ConstraintExtractor()
    return extractor.extract(ast_node)


def to_canonical_form(comparison: ComparisonNode) -> List[Constraint]:
    """
    Transform comparison to canonical LP constraints.
    
    Args:
        comparison: Comparison node
        
    Returns:
        List of constraints in canonical form
    """
    if comparison.operator == Operator.LE:
        # a ≤ b → a - b ≤ 0
        left_minus_right = BinaryOpNode(
            Operator.SUBTRACT,
            comparison.left,
            comparison.right
        )
        return [Constraint.from_expression(left_minus_right, '<=', 0.0)]
    
    elif comparison.operator == Operator.GE:
        # a ≥ b → -a + b ≤ 0
        neg_left = UnaryOpNode(Operator.NEGATE, comparison.left)
        neg_left_plus_right = BinaryOpNode(
            Operator.ADD,
            neg_left,
            comparison.right
        )
        return [Constraint.from_expression(neg_left_plus_right, '<=', 0.0)]
    
    elif comparison.operator == Operator.EQ:
        # a = b → a - b ≤ 0 AND -a + b ≤ 0
        left_minus_right = BinaryOpNode(
            Operator.SUBTRACT,
            comparison.left,
            comparison.right
        )
        neg_left = UnaryOpNode(Operator.NEGATE, comparison.left)
        neg_left_plus_right = BinaryOpNode(
            Operator.ADD,
            neg_left,
            comparison.right
        )
        return [
            Constraint.from_expression(left_minus_right, '<=', 0.0),
            Constraint.from_expression(neg_left_plus_right, '<=', 0.0)
        ]
    
    else:
        raise ValueError(f"Unsupported comparison operator: {comparison.operator}")


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_constraint_extraction():
    """Test constraint extraction functionality."""
    test_cases = [
        ("x <= y", 1, ["x - y <= 0"]),
        ("x >= y", 1, ["-x + y <= 0"]),
        ("x == y", 2, ["x - y <= 0", "-x + y <= 0"]),
        ("2*x + 3*y <= 5", 1, ["2*x + 3*y - 5 <= 0"]),
        ("x + y >= 10", 1, ["-x - y + 10 <= 0"]),
        ("x == 2*y + 3", 2, ["x - 2*y - 3 <= 0", "-x + 2*y + 3 <= 0"]),
    ]
    
    results = []
    for expr, expected_count, expected_strings in test_cases:
        try:
            constraints = extract_constraints(expr)
            passed = len(constraints) == expected_count
            constraint_strings = [str(c) for c in constraints]
            
            # Check if constraint strings match expected
            string_matches = all(
                any(expected in actual for expected in expected_strings)
                for actual in constraint_strings
            )
            
            results.append({
                'expression': expr,
                'constraints': constraints,
                'expected_count': expected_count,
                'actual_count': len(constraints),
                'passed': passed and string_matches,
                'constraint_strings': constraint_strings,
                'expected_strings': expected_strings
            })
        except Exception as e:
            results.append({
                'expression': expr,
                'error': str(e),
                'passed': False
            })
    
    return results


if __name__ == "__main__":
    """Test the constraint extractor module."""
    print("Constraint Extractor - Week 2 Implementation")
    print("=" * 60)
    
    # Run tests
    test_results = test_constraint_extraction()
    
    all_passed = True
    for result in test_results:
        if 'error' in result:
            print(f"✗ Expression: {result['expression']}")
            print(f"  Error: {result['error']}")
            all_passed = False
        else:
            status = "✓" if result['passed'] else "✗"
            print(f"{status} Expression: {result['expression']}")
            print(f"  Expected: {result['expected_count']} constraints")
            print(f"  Actual: {result['actual_count']} constraints")
            for i, constr in enumerate(result['constraint_strings']):
                print(f"    Constraint {i+1}: {constr}")
            if not result['passed']:
                all_passed = False
        print()
    
    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")
    
    # Example usage
    print("\nExample usage:")
    expr = "2*x + 3*y <= 10"
    constraints = extract_constraints(expr)
    print(f"Expression: {expr}")
    print(f"Constraints extracted: {len(constraints)}")
    for i, constraint in enumerate(constraints):
        print(f"  Constraint {i+1}: {constraint}")
        print(f"    Coefficients: {constraint.coefficients}")
        print(f"    Constant: {constraint.constant}")
        print(f"    Sense: {constraint.sense}")
