"""
DSL Parser for LP DSL Engine

This module parses DSL functions (DECISION, BOUND, OBJECTIVE) from AST.

Week 2 Requirements:
1. Parse DECISION(x, size=N) → expands to x1, x2, ..., xN
2. Parse BOUND(x, lower, upper) → variable bounds override
3. Parse OBJECTIVE(expr) → objective function for canonical LP
4. DSL detection pipeline

Design Principles:
- AST-based parsing only (no regex)
- Separation of concerns: DSL parsing vs constraint extraction
- Maintain backward compatibility
- Integration with existing AST parser
"""

from typing import Dict, List, Any, Optional, Union
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
class DSLDecision:
    """DSL DECISION function information."""
    variable_name: str
    size: int
    vector_variables: List[str]
    
    def __str__(self) -> str:
        if self.size > 1:
            return f"DECISION({self.variable_name}, size={self.size}) -> {self.vector_variables}"
        else:
            return f"DECISION({self.variable_name}) -> {self.variable_name}"


@dataclass
class DSLBound:
    """DSL BOUND function information."""
    variable_name: str
    lower: Optional[float]
    upper: Optional[float]
    
    def __str__(self) -> str:
        lower_str = str(self.lower) if self.lower is not None else "None"
        upper_str = str(self.upper) if self.upper is not None else "None"
        return f"BOUND({self.variable_name}, lower={lower_str}, upper={upper_str})"


@dataclass
class DSLObjective:
    """DSL OBJECTIVE function information."""
    expression: ExpressionNode
    
    def __str__(self) -> str:
        return f"OBJECTIVE({self.expression})"


@dataclass
class DSLInfo:
    """Container for all DSL information."""
    decisions: List[DSLDecision]
    bounds: List[DSLBound]
    objectives: List[DSLObjective]
    
    def __str__(self) -> str:
        parts = []
        if self.decisions:
            parts.append("Decisions:")
            for decision in self.decisions:
                parts.append(f"  - {decision}")
        if self.bounds:
            parts.append("Bounds:")
            for bound in self.bounds:
                parts.append(f"  - {bound}")
        if self.objectives:
            parts.append("Objectives:")
            for objective in self.objectives:
                parts.append(f"  - {objective}")
        return "\n".join(parts)


class DSLParser(ExpressionVisitor):
    """
    Parses DSL functions from AST.
    """
    
    def __init__(self):
        self.decisions: List[DSLDecision] = []
        self.bounds: List[DSLBound] = []
        self.objectives: List[DSLObjective] = []
    
    def visit_constant(self, node: ConstantNode) -> None:
        """Constants don't contain DSL functions."""
        pass
    
    def visit_variable(self, node: VariableNode) -> None:
        """Variables don't contain DSL functions."""
        pass
    
    def visit_binary_op(self, node: BinaryOpNode) -> None:
        """Visit both sides of binary operation."""
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_unary_op(self, node: UnaryOpNode) -> None:
        """Visit operand of unary operation."""
        node.operand.accept(self)
    
    def visit_function_call(self, node: FunctionCallNode) -> None:
        """Parse DSL function calls."""
        function_name = node.function_name.upper()
        
        if function_name == 'DECISION':
            decision = self._parse_decision(node)
            self.decisions.append(decision)
        elif function_name == 'BOUND':
            bound = self._parse_bound(node)
            self.bounds.append(bound)
        elif function_name == 'OBJECTIVE':
            objective = self._parse_objective(node)
            self.objectives.append(objective)
        
        # Continue visiting arguments for nested DSL functions
        for arg in node.arguments:
            arg.accept(self)
    
    def visit_parentheses(self, node: ParenthesesNode) -> None:
        """Visit expression inside parentheses."""
        node.expression.accept(self)
    
    def visit_comparison(self, node: ComparisonNode) -> None:
        """Visit both sides of comparison."""
        node.left.accept(self)
        node.right.accept(self)
    
    def _parse_decision(self, node: FunctionCallNode) -> DSLDecision:
        """
        Parse DECISION(x, size=N) function call.
        
        Args:
            node: FunctionCallNode for DECISION
            
        Returns:
            DSLDecision object
            
        Raises:
            ValueError: If DECISION syntax is invalid
        """
        if len(node.arguments) < 1:
            raise ValueError("DECISION requires at least variable name")
        
        # First argument is variable name
        var_name_node = node.arguments[0]
        if not isinstance(var_name_node, VariableNode):
            raise ValueError("DECISION first argument must be variable name")
        
        var_name = var_name_node.name
        size = 1  # Default size
        
        # Check for size parameter
        if len(node.arguments) > 1:
            # Look for keyword argument size=N
            for i in range(1, len(node.arguments)):
                arg = node.arguments[i]
                if isinstance(arg, BinaryOpNode) and arg.operator == Operator.EQ:
                    if isinstance(arg.left, VariableNode) and arg.left.name == 'size':
                        if isinstance(arg.right, ConstantNode):
                            size = int(arg.right.value)
                        else:
                            raise ValueError("DECISION size parameter must be constant")
        
        # Generate vector variable names
        vector_vars = []
        if size > 1:
            vector_vars = [f"{var_name}{i+1}" for i in range(size)]
        else:
            vector_vars = [var_name]
        
        return DSLDecision(
            variable_name=var_name,
            size=size,
            vector_variables=vector_vars
        )
    
    def _parse_bound(self, node: FunctionCallNode) -> DSLBound:
        """
        Parse BOUND(x, lower, upper) function call.
        
        Args:
            node: FunctionCallNode for BOUND
            
        Returns:
            DSLBound object
            
        Raises:
            ValueError: If BOUND syntax is invalid
        """
        if len(node.arguments) < 3:
            raise ValueError("BOUND requires variable name, lower bound, and upper bound")
        
        # First argument is variable name
        var_name_node = node.arguments[0]
        if not isinstance(var_name_node, VariableNode):
            raise ValueError("BOUND first argument must be variable name")
        
        var_name = var_name_node.name
        
        # Parse lower bound
        lower_node = node.arguments[1]
        lower = self._parse_bound_value(lower_node)
        
        # Parse upper bound
        upper_node = node.arguments[2]
        upper = self._parse_bound_value(upper_node)
        
        return DSLBound(
            variable_name=var_name,
            lower=lower,
            upper=upper
        )
    
    def _parse_bound_value(self, node: ExpressionNode) -> Optional[float]:
        """
        Parse bound value (constant or None).
        
        Args:
            node: Expression node for bound value
            
        Returns:
            Float value or None
            
        Raises:
            ValueError: If bound value is invalid
        """
        if isinstance(node, ConstantNode):
            return node.value
        elif isinstance(node, UnaryOpNode) and node.operator == Operator.NEGATE:
            # Handle negative numbers like -5, -10.5
            operand = node.operand
            if isinstance(operand, ConstantNode):
                return -operand.value
            else:
                raise ValueError(f"Invalid bound value: {node}")
        elif isinstance(node, VariableNode):
            if node.name.upper() == 'NONE':
                return None
            else:
                raise ValueError(f"Invalid bound value: {node.name}")
        else:
            raise ValueError(f"Invalid bound value: {node}")
    
    def _parse_objective(self, node: FunctionCallNode) -> DSLObjective:
        """
        Parse OBJECTIVE(expr) function call.
        
        Args:
            node: FunctionCallNode for OBJECTIVE
            
        Returns:
            DSLObjective object
            
        Raises:
            ValueError: If OBJECTIVE syntax is invalid
        """
        if len(node.arguments) != 1:
            raise ValueError("OBJECTIVE requires exactly one expression argument")
        
        expr = node.arguments[0]
        return DSLObjective(expression=expr)
    
    def extract(self, node: ExpressionNode) -> DSLInfo:
        """
        Extract all DSL information from AST.
        
        Args:
            node: Root node of AST
            
        Returns:
            DSLInfo object containing all DSL information
        """
        self.decisions.clear()
        self.bounds.clear()
        self.objectives.clear()
        node.accept(self)
        return DSLInfo(
            decisions=self.decisions.copy(),
            bounds=self.bounds.copy(),
            objectives=self.objectives.copy()
        )


class DSLDetector(ExpressionVisitor):
    """
    Detects DSL functions in AST without parsing details.
    """
    
    def __init__(self):
        self.has_dsl = False
        self.dsl_functions: List[str] = []
    
    def visit_constant(self, node: ConstantNode) -> None:
        pass
    
    def visit_variable(self, node: VariableNode) -> None:
        pass
    
    def visit_binary_op(self, node: BinaryOpNode) -> None:
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_unary_op(self, node: UnaryOpNode) -> None:
        node.operand.accept(self)
    
    def visit_function_call(self, node: FunctionCallNode) -> None:
        function_name = node.function_name.upper()
        if function_name in ['DECISION', 'BOUND', 'OBJECTIVE']:
            self.has_dsl = True
            self.dsl_functions.append(function_name)
        
        # Continue visiting arguments
        for arg in node.arguments:
            arg.accept(self)
    
    def visit_parentheses(self, node: ParenthesesNode) -> None:
        node.expression.accept(self)
    
    def visit_comparison(self, node: ComparisonNode) -> None:
        node.left.accept(self)
        node.right.accept(self)
    
    def detect(self, node: ExpressionNode) -> Dict[str, Any]:
        """
        Detect DSL functions in AST.
        
        Args:
            node: Root node of AST
            
        Returns:
            Dictionary with detection results
        """
        self.has_dsl = False
        self.dsl_functions.clear()
        node.accept(self)
        return {
            'has_dsl': self.has_dsl,
            'dsl_functions': self.dsl_functions.copy(),
            'dsl_count': len(self.dsl_functions)
        }


def parse_dsl(expression: str) -> DSLInfo:
    """
    Parse DSL functions from expression string.
    
    Args:
        expression: String containing mathematical expression
        
    Returns:
        DSLInfo object containing all DSL information
        
    Raises:
        ValueError: If expression cannot be parsed
    """
    try:
        from .ast_expression_parser import parse_expression
    except ImportError:
        from ast_expression_parser import parse_expression
    ast_node = parse_expression(expression)
    parser = DSLParser()
    return parser.extract(ast_node)


def detect_dsl(expression: str) -> Dict[str, Any]:
    """
    Detect DSL functions in expression string.
    
    Args:
        expression: String containing mathematical expression
        
    Returns:
        Dictionary with detection results
        
    Raises:
        ValueError: If expression cannot be parsed
    """
    try:
        from .ast_expression_parser import parse_expression
    except ImportError:
        from ast_expression_parser import parse_expression
    ast_node = parse_expression(expression)
    detector = DSLDetector()
    return detector.detect(ast_node)


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_dsl_parsing():
    """Test DSL parsing functionality."""
    test_cases = [
        ("DECISION(x)", 1, 0, 0),
        ("DECISION(x, size=3)", 1, 0, 0),
        ("BOUND(x, 0, 10)", 0, 1, 0),
        ("OBJECTIVE(2*x + 3*y)", 0, 0, 1),
        ("DECISION(x, size=2) AND BOUND(x1, 0, None)", 1, 1, 0),
        ("OBJECTIVE(x) AND DECISION(y, size=3) AND BOUND(y1, 0, 5)", 1, 1, 1),
    ]
    
    results = []
    for expr, expected_decisions, expected_bounds, expected_objectives in test_cases:
        try:
            dsl_info = parse_dsl(expr)
            passed = (len(dsl_info.decisions) == expected_decisions and
                     len(dsl_info.bounds) == expected_bounds and
                     len(dsl_info.objectives) == expected_objectives)
            
            results.append({
                'expression': expr,
                'dsl_info': dsl_info,
                'expected_decisions': expected_decisions,
                'expected_bounds': expected_bounds,
                'expected_objectives': expected_objectives,
                'actual_decisions': len(dsl_info.decisions),
                'actual_bounds': len(dsl_info.bounds),
                'actual_objectives': len(dsl_info.objectives),
                'passed': passed
            })
        except Exception as e:
            results.append({
                'expression': expr,
                'error': str(e),
                'passed': False
            })
    
    return results


if __name__ == "__main__":
    """Test the DSL parser module."""
    print("DSL Parser - Week 2 Implementation")
    print("=" * 60)
    
    # Run tests
    test_results = test_dsl_parsing()
    
    all_passed = True
    for result in test_results:
        if 'error' in result:
            print(f"✗ Expression: {result['expression']}")
            print(f"  Error: {result['error']}")
            all_passed = False
        else:
            status = "✓" if result['passed'] else "✗"
            print(f"{status} Expression: {result['expression']}")
            print(f"  Expected: {result['expected_decisions']} decisions, "
                  f"{result['expected_bounds']} bounds, "
                  f"{result['expected_objectives']} objectives")
            print(f"  Actual: {result['actual_decisions']} decisions, "
                  f"{result['actual_bounds']} bounds, "
                  f"{result['actual_objectives']} objectives")
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
    
    # Test DECISION expansion
    expr1 = "DECISION(x, size=3)"
    dsl_info1 = parse_dsl(expr1)
    print(f"Expression: {expr1}")
    print(f"DSL Info:\n{dsl_info1}")
    
    # Test BOUND parsing
    expr2 = "BOUND(y, 0, None)"
    dsl_info2 = parse_dsl(expr2)
    print(f"\nExpression: {expr2}")
    print(f"DSL Info:\n{dsl_info2}")
    
    # Test OBJECTIVE parsing
    expr3 = "OBJECTIVE(2*x + 3*y)"
    dsl_info3 = parse_dsl(expr3)
    print(f"\nExpression: {expr3}")
    print(f"DSL Info:\n{dsl_info3}")
    
    # Test detection
    expr4 = "DECISION(x) AND BOUND(x, 0, 10) AND OBJECTIVE(x)"
    detection = detect_dsl(expr4)
    print(f"\nExpression: {expr4}")
    print(f"Detection: {detection}")
