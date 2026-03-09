"""
AST Expression Parser for LP DSL Engine

This module provides an AST-based parser for linear programming expressions.
It parses mathematical expressions into an abstract syntax tree (AST) that
can be evaluated, analyzed, and transformed for LP matrix construction.

Week 1 Deliverables:
1. AST node hierarchy for LP expressions
2. Minimal parser for linear expressions only (+, -, *, /, parentheses)
3. Support for linear expressions only
4. Unit tests for expression parsing

Design Principles:
- Simple and focused on linear expressions
- Extensible for future enhancements
- Integration with existing formula runtime
- Backward compatibility with dual parsing system
"""

import ast
import html
from typing import Dict, Any, Optional, Union, List, Set
from enum import Enum
from dataclasses import dataclass


# ============================================================================
# AST NODE HIERARCHY
# ============================================================================

class NodeType(Enum):
    """Types of AST nodes."""
    CONSTANT = "constant"
    VARIABLE = "variable"
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    FUNCTION_CALL = "function_call"
    PARENTHESES = "parentheses"
    COMPARISON = "comparison"


class Operator(Enum):
    """Supported operators for linear expressions."""
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    NEGATE = "-"  # Unary minus
    LE = "<="    # Less than or equal
    GE = ">="    # Greater than or equal
    EQ = "=="    # Equal


@dataclass
class ExpressionNode:
    """Base class for all AST nodes."""
    
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        """Accept a visitor for traversal."""
        raise NotImplementedError("Subclasses must implement accept()")
    
    def __str__(self) -> str:
        """String representation for debugging."""
        raise NotImplementedError("Subclasses must implement __str__()")
    
    @property
    def node_type(self) -> NodeType:
        """Get the node type based on the class."""
        if isinstance(self, ConstantNode):
            return NodeType.CONSTANT
        elif isinstance(self, VariableNode):
            return NodeType.VARIABLE
        elif isinstance(self, BinaryOpNode):
            return NodeType.BINARY_OP
        elif isinstance(self, UnaryOpNode):
            return NodeType.UNARY_OP
        elif isinstance(self, FunctionCallNode):
            return NodeType.FUNCTION_CALL
        elif isinstance(self, ParenthesesNode):
            return NodeType.PARENTHESES
        elif isinstance(self, ComparisonNode):
            return NodeType.COMPARISON
        else:
            raise ValueError(f"Unknown node type: {type(self).__name__}")


@dataclass
class ConstantNode(ExpressionNode):
    """Node representing a constant numeric value."""
    value: float
    
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        return visitor.visit_constant(self)
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass
class VariableNode(ExpressionNode):
    """Node representing a variable."""
    name: str
    
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        return visitor.visit_variable(self)
    
    def __str__(self) -> str:
        return self.name


@dataclass
class BinaryOpNode(ExpressionNode):
    """Node representing a binary operation."""
    operator: Operator
    left: ExpressionNode
    right: ExpressionNode
    
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        return visitor.visit_binary_op(self)
    
    def __str__(self) -> str:
        return f"({self.left} {self.operator.value} {self.right})"


@dataclass
class UnaryOpNode(ExpressionNode):
    """Node representing a unary operation (negation)."""
    operator: Operator
    operand: ExpressionNode
    
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        return visitor.visit_unary_op(self)
    
    def __str__(self) -> str:
        return f"({self.operator.value}{self.operand})"


@dataclass
class FunctionCallNode(ExpressionNode):
    """Node representing a function call (for future extension)."""
    function_name: str
    arguments: List[ExpressionNode]
    
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        return visitor.visit_function_call(self)
    
    def __str__(self) -> str:
        args = ", ".join(str(arg) for arg in self.arguments)
        return f"{self.function_name}({args})"


@dataclass
class ParenthesesNode(ExpressionNode):
    """Node representing parentheses for grouping."""
    expression: ExpressionNode
    
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        return visitor.visit_parentheses(self)
    
    def __str__(self) -> str:
        return f"({self.expression})"


@dataclass
class ComparisonNode(ExpressionNode):
    """Node representing a comparison operation (<=, >=, ==)."""
    operator: Operator
    left: ExpressionNode
    right: ExpressionNode
    
    def accept(self, visitor: 'ExpressionVisitor') -> Any:
        return visitor.visit_comparison(self)
    
    def __str__(self) -> str:
        return f"({self.left} {self.operator.value} {self.right})"


# ============================================================================
# EXPRESSION VISITOR PATTERN
# ============================================================================

class ExpressionVisitor:
    """Visitor pattern for traversing and processing AST nodes."""
    
    def visit_constant(self, node: ConstantNode) -> Any:
        """Visit a constant node."""
        raise NotImplementedError("Subclasses must implement visit_constant()")
    
    def visit_variable(self, node: VariableNode) -> Any:
        """Visit a variable node."""
        raise NotImplementedError("Subclasses must implement visit_variable()")
    
    def visit_binary_op(self, node: BinaryOpNode) -> Any:
        """Visit a binary operation node."""
        raise NotImplementedError("Subclasses must implement visit_binary_op()")
    
    def visit_unary_op(self, node: UnaryOpNode) -> Any:
        """Visit a unary operation node."""
        raise NotImplementedError("Subclasses must implement visit_unary_op()")
    
    def visit_function_call(self, node: FunctionCallNode) -> Any:
        """Visit a function call node."""
        raise NotImplementedError("Subclasses must implement visit_function_call()")
    
    def visit_parentheses(self, node: ParenthesesNode) -> Any:
        """Visit a parentheses node."""
        raise NotImplementedError("Subclasses must implement visit_parentheses()")
    
    def visit_comparison(self, node: ComparisonNode) -> Any:
        """Visit a comparison node."""
        raise NotImplementedError("Subclasses must implement visit_comparison()")


# ============================================================================
# AST PARSER
# ============================================================================

class ASTExpressionParser:
    """
    Parser that converts mathematical expressions into AST.
    
    This parser focuses on linear expressions only:
    - Constants: 1, 2.5, -3.14
    - Variables: x, y, x1, x2
    - Binary operators: +, -, *, /
    - Unary operators: - (negation)
    - Parentheses: ( )
    
    Note: For Week 1, we only support linear expressions.
    Non-linear operations (pow, sqrt, etc.) will be added in future phases.
    """
    
    def __init__(self):
        """Initialize the parser."""
        self._operator_precedence = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2,
            'u-': 3,  # Unary minus
        }
    
    def parse(self, expression: str) -> ExpressionNode:
        """
        Parse a mathematical expression into an AST.
        
        Args:
            expression: String containing mathematical expression
            
        Returns:
            Root node of the AST
            
        Raises:
            ValueError: If expression cannot be parsed
            SyntaxError: If expression has syntax errors
        """
        # Decode HTML entities (for compatibility with existing system)
        decoded_expr = html.unescape(expression)
        
        try:
            # Parse using Python's ast module as a starting point
            python_ast = ast.parse(decoded_expr, mode='eval')
            
            # Convert Python AST to our custom AST
            return self._convert_ast(python_ast.body)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in expression '{expression}': {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse expression '{expression}': {e}")
    
    def _convert_ast(self, node: ast.AST) -> ExpressionNode:
        """
        Convert Python AST node to our custom AST node.
        
        Args:
            node: Python AST node
            
        Returns:
            Custom AST node
        """
        if isinstance(node, ast.Expression):
            return self._convert_ast(node.body)
        
        elif isinstance(node, ast.Constant):
            # Handle numeric constants and None
            # Check if value is numeric (int or float) or None
            if node.value is None:
                # For DSL compatibility, treat None as a special constant
                # The DSL parser will handle None as a bound value
                # We'll represent it as a VariableNode with name 'NONE' 
                # to match the DSL parser's expectation
                return VariableNode(name='NONE')
            elif isinstance(node.value, (int, float)):
                try:
                    value = float(node.value)
                    return ConstantNode(value=value)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid constant value: {node.value}")
            else:
                raise ValueError(f"Invalid constant value: {node.value} (type: {type(node.value).__name__})")
        
        elif isinstance(node, ast.Name):
            # Handle variable names
            return VariableNode(name=node.id)
        
        elif isinstance(node, ast.BinOp):
            # Handle binary operations
            left = self._convert_ast(node.left)
            right = self._convert_ast(node.right)
            
            # Map Python operators to our Operator enum
            if isinstance(node.op, ast.Add):
                operator = Operator.ADD
            elif isinstance(node.op, ast.Sub):
                operator = Operator.SUBTRACT
            elif isinstance(node.op, ast.Mult):
                operator = Operator.MULTIPLY
            elif isinstance(node.op, ast.Div):
                operator = Operator.DIVIDE
            else:
                raise ValueError(f"Unsupported binary operator: {node.op}")
            
            return BinaryOpNode(operator=operator, left=left, right=right)
        
        elif isinstance(node, ast.UnaryOp):
            # Handle unary operations (only negation supported for linear expressions)
            if isinstance(node.op, ast.USub):
                operand = self._convert_ast(node.operand)
                return UnaryOpNode(operator=Operator.NEGATE, operand=operand)
            else:
                raise ValueError(f"Unsupported unary operator: {node.op}")
        
        elif isinstance(node, ast.Call):
            # Handle function calls (for future extension)
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are supported")
            
            function_name = node.func.id
            
            # Convert positional arguments
            arguments = [self._convert_ast(arg) for arg in node.args]
            
            # Convert keyword arguments to BinaryOpNode with EQ operator
            for keyword in node.keywords:
                # keyword.arg is the argument name (e.g., 'size')
                # keyword.value is the value expression
                if keyword.arg is None:  # **kwargs syntax
                    raise ValueError("**kwargs syntax not supported")
                
                # Create a BinaryOpNode representing arg=value
                arg_name_node = VariableNode(name=keyword.arg)
                arg_value_node = self._convert_ast(keyword.value)
                eq_node = BinaryOpNode(
                    operator=Operator.EQ,
                    left=arg_name_node,
                    right=arg_value_node
                )
                arguments.append(eq_node)
            
            # For Week 1, we only support linear expressions
            # Function calls will be properly handled in future phases
            return FunctionCallNode(function_name=function_name, arguments=arguments)
        
        elif isinstance(node, ast.Compare):
            # Handle comparison expressions (Week 2)
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ValueError("Only single comparisons supported (e.g., x <= y, not x <= y <= z)")
            
            left = self._convert_ast(node.left)
            right = self._convert_ast(node.comparators[0])
            operator = self._map_comparison_operator(node.ops[0])
            
            return ComparisonNode(operator=operator, left=left, right=right)
        
        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")
    
    def _map_comparison_operator(self, op_node: ast.cmpop) -> Operator:
        """
        Map Python AST comparison operator to our Operator enum.
        
        Args:
            op_node: Python AST comparison operator node
            
        Returns:
            Corresponding Operator enum value
        """
        if isinstance(op_node, ast.LtE):
            return Operator.LE
        elif isinstance(op_node, ast.GtE):
            return Operator.GE
        elif isinstance(op_node, ast.Eq):
            return Operator.EQ
        else:
            raise ValueError(f"Unsupported comparison operator: {op_node}")


# ============================================================================
# EXPRESSION EVALUATOR
# ============================================================================

class ExpressionEvaluator(ExpressionVisitor):
    """
    Evaluates AST nodes with a given variable context.
    
    This evaluator computes the numeric value of an expression
    given values for all variables in the expression.
    """
    
    def __init__(self, context: Dict[str, float]):
        """
        Initialize evaluator with variable context.
        
        Args:
            context: Dictionary mapping variable names to values
        """
        self.context = context
    
    def visit_constant(self, node: ConstantNode) -> float:
        """Evaluate constant node."""
        return node.value
    
    def visit_variable(self, node: VariableNode) -> float:
        """Evaluate variable node."""
        if node.name not in self.context:
            raise KeyError(f"Variable '{node.name}' not found in context")
        return self.context[node.name]
    
    def visit_binary_op(self, node: BinaryOpNode) -> float:
        """Evaluate binary operation node."""
        left_value = node.left.accept(self)
        right_value = node.right.accept(self)
        
        if node.operator == Operator.ADD:
            return left_value + right_value
        elif node.operator == Operator.SUBTRACT:
            return left_value - right_value
        elif node.operator == Operator.MULTIPLY:
            return left_value * right_value
        elif node.operator == Operator.DIVIDE:
            if right_value == 0:
                raise ZeroDivisionError("Division by zero")
            return left_value / right_value
        else:
            raise ValueError(f"Unknown operator: {node.operator}")
    
    def visit_unary_op(self, node: UnaryOpNode) -> float:
        """Evaluate unary operation node."""
        operand_value = node.operand.accept(self)
        
        if node.operator == Operator.NEGATE:
            return -operand_value
        else:
            raise ValueError(f"Unknown unary operator: {node.operator}")
    
    def visit_function_call(self, node: FunctionCallNode) -> float:
        """Evaluate function call node."""
        # For Week 1, we don't support function calls in linear expressions
        raise ValueError(f"Function calls not supported in linear expressions: {node.function_name}")
    
    def visit_parentheses(self, node: ParenthesesNode) -> float:
        """Evaluate parentheses node."""
        return node.expression.accept(self)


# ============================================================================
# VARIABLE EXTRACTOR
# ============================================================================

class VariableExtractor(ExpressionVisitor):
    """
    Extracts all variable names from an AST.
    """
    
    def __init__(self):
        self.variables: Set[str] = set()
    
    def visit_constant(self, node: ConstantNode) -> None:
        """Constant nodes have no variables."""
        pass
    
    def visit_variable(self, node: VariableNode) -> None:
        """Add variable name to set."""
        self.variables.add(node.name)
    
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
        """Visit both sides of comparison."""
        node.left.accept(self)
        node.right.accept(self)
    
    def extract(self, node: ExpressionNode) -> Set[str]:
        """
        Extract all variable names from the AST.
        
        Args:
            node: Root node of AST
            
        Returns:
            Set of variable names
        """
        self.variables.clear()
        node.accept(self)
        return self.variables.copy()


# ============================================================================
# EXPRESSION SIMPLIFIER (Basic)
# ============================================================================

class ExpressionSimplifier(ExpressionVisitor):
    """
    Simplifies AST by performing constant folding and basic simplifications.
    
    For Week 1, this performs basic constant folding:
    - 2 + 3 → 5
    - x + 0 → x
    - x * 1 → x
    - x * 0 → 0
    """
    
    def visit_constant(self, node: ConstantNode) -> ExpressionNode:
        """Constant nodes are already simplified."""
        return node
    
    def visit_variable(self, node: VariableNode) -> ExpressionNode:
        """Variable nodes are already simplified."""
        return node
    
    def visit_binary_op(self, node: BinaryOpNode) -> ExpressionNode:
        """Simplify binary operation."""
        left = node.left.accept(self)
        right = node.right.accept(self)
        
        # Constant folding: if both sides are constants, compute the result
        if isinstance(left, ConstantNode) and isinstance(right, ConstantNode):
            try:
                evaluator = ExpressionEvaluator({})
                result = evaluator.visit_binary_op(BinaryOpNode(operator=node.operator, left=left, right=right))
                return ConstantNode(value=result)
            except (ZeroDivisionError, ValueError):
                # If computation fails, return the original node
                return BinaryOpNode(operator=node.operator, left=left, right=right)
        
        # Simplification rules
        if node.operator == Operator.ADD:
            # x + 0 → x
            if isinstance(right, ConstantNode) and right.value == 0:
                return left
            # 0 + x → x
            if isinstance(left, ConstantNode) and left.value == 0:
                return right
        
        elif node.operator == Operator.SUBTRACT:
            # x - 0 → x
            if isinstance(right, ConstantNode) and right.value == 0:
                return left
            # 0 - x → -x
            if isinstance(left, ConstantNode) and left.value == 0:
                return UnaryOpNode(Operator.NEGATE, right)
        
        elif node.operator == Operator.MULTIPLY:
            # x * 1 → x
            if isinstance(right, ConstantNode) and right.value == 1:
                return left
            # 1 * x → x
            if isinstance(left, ConstantNode) and left.value == 1:
                return right
            # x * 0 → 0
            if (isinstance(left, ConstantNode) and left.value == 0) or \
               (isinstance(right, ConstantNode) and right.value == 0):
                return ConstantNode(value=0.0)
        
        elif node.operator == Operator.DIVIDE:
            # x / 1 → x
            if isinstance(right, ConstantNode) and right.value == 1:
                return left
            # 0 / x → 0 (if x ≠ 0)
            if isinstance(left, ConstantNode) and left.value == 0:
                return ConstantNode(value=0.0)
        
        return BinaryOpNode(node.operator, left, right)
    
    def visit_unary_op(self, node: UnaryOpNode) -> ExpressionNode:
        """Simplify unary operation."""
        operand = node.operand.accept(self)
        
        # -(-x) → x
        if isinstance(operand, UnaryOpNode) and operand.operator == Operator.NEGATE:
            return operand.operand
        
        # -(constant) → constant with negated value
        if isinstance(operand, ConstantNode):
            return ConstantNode(value=-operand.value)
        
        return UnaryOpNode(node.operator, operand)
    
    def visit_function_call(self, node: FunctionCallNode) -> ExpressionNode:
        """Simplify function call arguments."""
        simplified_args = [arg.accept(self) for arg in node.arguments]
        return FunctionCallNode(node.function_name, simplified_args)
    
    def visit_parentheses(self, node: ParenthesesNode) -> ExpressionNode:
        """Simplify expression inside parentheses."""
        simplified_expr = node.expression.accept(self)
        # Remove unnecessary parentheses
        if isinstance(simplified_expr, (ConstantNode, VariableNode, UnaryOpNode)):
            return simplified_expr
        return ParenthesesNode(simplified_expr)


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def parse_expression(expression: str) -> ExpressionNode:
    """
    Parse a mathematical expression into an AST.
    
    Args:
        expression: String containing mathematical expression
        
    Returns:
        Root node of the AST
        
    Raises:
        ValueError: If expression cannot be parsed
        SyntaxError: If expression has syntax errors
    """
    parser = ASTExpressionParser()
    return parser.parse(expression)


def evaluate_expression(expression: str, context: Dict[str, float]) -> float:
    """
    Evaluate a mathematical expression with given variable values.
    
    Args:
        expression: String containing mathematical expression
        context: Dictionary mapping variable names to values
        
    Returns:
        Numeric result of evaluation
        
    Raises:
        ValueError: If expression cannot be parsed or evaluated
        KeyError: If required variables are missing from context
        ZeroDivisionError: If division by zero occurs
    """
    parser = ASTExpressionParser()
    ast_node = parser.parse(expression)
    evaluator = ExpressionEvaluator(context)
    return ast_node.accept(evaluator)


def extract_variables(expression: str) -> Set[str]:
    """
    Extract all variable names from an expression.
    
    Args:
        expression: String containing mathematical expression
        
    Returns:
        Set of variable names used in the expression
        
    Raises:
        ValueError: If expression cannot be parsed
    """
    parser = ASTExpressionParser()
    ast_node = parser.parse(expression)
    extractor = VariableExtractor()
    return extractor.extract(ast_node)


def simplify_expression(expression: str) -> str:
    """
    Simplify a mathematical expression.
    
    Args:
        expression: String containing mathematical expression
        
    Returns:
        Simplified expression as string
        
    Raises:
        ValueError: If expression cannot be parsed
    """
    parser = ASTExpressionParser()
    ast_node = parser.parse(expression)
    simplifier = ExpressionSimplifier()
    simplified_node = ast_node.accept(simplifier)
    return str(simplified_node)


# ============================================================================
# INTEGRATION WITH EXISTING FORMULA RUNTIME
# ============================================================================

def integrate_with_formula_runtime():
    """
    Demonstrate integration with existing formula runtime.
    
    This function shows how the AST parser can be integrated
    with the existing formula_runtime.py module.
    """
    # Example usage that matches existing formula runtime patterns
    example_expr = "2*x + 3*y - 4"
    context = {"x": 5.0, "y": 2.0}
    
    try:
        # Parse and evaluate using our AST parser
        result = evaluate_expression(example_expr, context)
        print(f"Expression: {example_expr}")
        print(f"Context: {context}")
        print(f"Result: {result}")
        
        # Extract variables
        variables = extract_variables(example_expr)
        print(f"Variables: {variables}")
        
        # Simplify expression
        simplified = simplify_expression(example_expr)
        print(f"Simplified: {simplified}")
        
        return result
    except Exception as e:
        print(f"Error: {e}")
        raise


# ============================================================================
# MAIN MODULE TEST
# ============================================================================

if __name__ == "__main__":
    """Test the AST expression parser module."""
    print("AST Expression Parser - Week 1 Implementation")
    print("=" * 60)
    
    # Test basic parsing and evaluation
    test_cases = [
        ("2 + 3", {}),
        ("x + y", {"x": 5, "y": 3}),
        ("2*x - 3*y", {"x": 4, "y": 1}),
        ("(x + y) * 2", {"x": 3, "y": 4}),
        ("-x + 5", {"x": 2}),
        ("x / 2", {"x": 10}),
    ]
    
    for expr, context in test_cases:
        try:
            result = evaluate_expression(expr, context)
            variables = extract_variables(expr)
            simplified = simplify_expression(expr)
            print(f"\nExpression: {expr}")
            print(f"  Context: {context}")
            print(f"  Variables: {variables}")
            print(f"  Result: {result}")
            print(f"  Simplified: {simplified}")
        except Exception as e:
            print(f"\nExpression: {expr}")
            print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print("Week 1 AST Parser Implementation Complete")
