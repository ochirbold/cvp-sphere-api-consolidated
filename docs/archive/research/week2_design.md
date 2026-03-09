# Week 2 Implementation Design

## I. DESIGN CHANGES

### 1. Unicode Normalization Layer Design

**Objective**: Support both ASCII and Unicode comparison operators with normalization to ASCII before AST parsing.

**Design**:

- Create a `UnicodeNormalizer` class that handles:
  - Unicode operator mapping: `≤` → `<=`, `≥` → `>=`, `＝` → `==`
  - UTF-8 decoding with fallback strategies
  - Line ending normalization: CRLF → LF
  - Tab normalization: tabs → spaces
  - HTML entity decoding (existing functionality)

**Implementation Strategy**:

- Isolate normalization in a separate module `unicode_normalizer.py`
- Apply normalization BEFORE any parsing occurs
- Maintain backward compatibility with existing ASCII operators
- Use Python's `unicodedata.normalize('NFKC', text)` for Unicode normalization

### 2. AST Updates (ComparisonNode + DSL Support)

**Objective**: Extend AST to support comparison operators and DSL function parsing.

**New AST Node Types**:

- `ComparisonNode`: Represents comparison expressions (a <= b, a >= b, a == b)
- `ConstraintNode`: Represents extracted constraints with canonical form
- `DSLFunctionNode`: Base class for DSL functions (DECISION, BOUND, OBJECTIVE)

**Operator Enum Extension**:

```python
class Operator(Enum):
    # Existing operators...
    LE = "<="    # Less than or equal
    GE = ">="    # Greater than or equal
    EQ = "=="    # Equal
    LE_UNICODE = "≤"  # Unicode less than or equal
    GE_UNICODE = "≥"  # Unicode greater than or equal
    EQ_UNICODE = "＝"  # Unicode equal
```

**ComparisonNode Structure**:

```python
@dataclass
class ComparisonNode(ExpressionNode):
    operator: Operator
    left: ExpressionNode
    right: ExpressionNode
    # Methods for canonical transformation
```

### 3. Constraint Model Design

**Objective**: Extract constraints from comparison expressions and transform to canonical LP form.

**Constraint Representation**:

```python
@dataclass
class Constraint:
    """Canonical LP constraint: a·x ≤ b"""
    coefficients: Dict[str, float]  # variable -> coefficient
    constant: float                 # right-hand side constant
    sense: str                     # '<=', '>=', '=='
    original_expr: str             # Original expression for debugging
```

**Constraint Extraction Pipeline**:

1. Parse expression with AST
2. Identify ComparisonNode in AST
3. Extract left and right expressions
4. Transform to canonical form:
   - `a ≤ b` → `a - b ≤ 0`
   - `a ≥ b` → `-a + b ≤ 0`
   - `a = b` → two constraints: `a - b ≤ 0` AND `-a + b ≤ 0`

### 4. Canonical Transformation Design

**Canonical Rules (MANDATORY)**:

- `a ≤ b` → `a - b ≤ 0`
- `a ≥ b` → `-a + b ≤ 0`
- `a = b` → two constraints: `a - b ≤ 0` AND `-a + b ≤ 0`

**Transformation Algorithm**:

1. Parse comparison expression
2. Extract left and right expressions
3. Based on operator:
   - For `≤`: left - right ≤ 0
   - For `≥`: -left + right ≤ 0
   - For `=`: create two constraints
4. Simplify resulting expression
5. Extract coefficients and constant

### 5. DSL Parsing Design (DECISION size logic)

**Objective**: Parse DSL functions with special handling for DECISION size parameter.

**DSL Function Types**:

1. `DECISION(x, size=N)` → expands to `x1, x2, ..., xN`
2. `BOUND(x, lower, upper)` → variable bounds override
3. `OBJECTIVE(expr)` → objective function for canonical LP

**DECISION Expansion Logic**:

- Parse `DECISION(x, size=3)` → generates variables `['x1', 'x2', 'x3']`
- Store metadata: base name, size, vector variables
- Integrate with existing variable extraction

**DSL Detection Pipeline**:

1. Pre-process expression to identify DSL function calls
2. Parse function name and arguments
3. Apply special handling based on function type
4. Return structured DSL information

## II. PSEUDO CODE

### 1. Unicode Normalization Layer

```python
class UnicodeNormalizer:
    def __init__(self):
        self.unicode_to_ascii = {
            '≤': '<=',
            '≥': '>=',
            '＝': '==',
            # Add other Unicode math operators as needed
        }

    def normalize(self, text: str) -> str:
        # 1. Ensure UTF-8 decoding
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')

        # 2. Normalize Unicode characters
        text = unicodedata.normalize('NFKC', text)

        # 3. Replace Unicode operators with ASCII
        for unicode_op, ascii_op in self.unicode_to_ascii.items():
            text = text.replace(unicode_op, ascii_op)

        # 4. Normalize line endings (Windows compatibility)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 5. Normalize tabs to spaces (optional, for consistency)
        text = text.replace('\t', '    ')

        return text
```

### 2. Comparison Parsing via AST

```python
class ASTExpressionParser:
    def _convert_ast(self, node: ast.AST) -> ExpressionNode:
        if isinstance(node, ast.Compare):
            # Handle comparison expressions
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ValueError("Only single comparisons supported")

            left = self._convert_ast(node.left)
            right = self._convert_ast(node.comparators[0])
            op = self._map_comparison_operator(node.ops[0])

            return ComparisonNode(operator=op, left=left, right=right)
        # ... existing code

    def _map_comparison_operator(self, op_node: ast.cmpop) -> Operator:
        if isinstance(op_node, ast.LtE):
            return Operator.LE
        elif isinstance(op_node, ast.GtE):
            return Operator.GE
        elif isinstance(op_node, ast.Eq):
            return Operator.EQ
        else:
            raise ValueError(f"Unsupported comparison operator: {op_node}")
```

### 3. Constraint Extraction

```python
class ConstraintExtractor(ExpressionVisitor):
    def __init__(self):
        self.constraints = []

    def visit_comparison(self, node: ComparisonNode) -> List[Constraint]:
        # Transform to canonical form
        if node.operator == Operator.LE:
            # a ≤ b → a - b ≤ 0
            expr = BinaryOpNode(Operator.SUBTRACT, node.left, node.right)
            constant = 0.0
            sense = '<='
        elif node.operator == Operator.GE:
            # a ≥ b → -a + b ≤ 0
            neg_left = UnaryOpNode(Operator.NEGATE, node.left)
            expr = BinaryOpNode(Operator.ADD, neg_left, node.right)
            constant = 0.0
            sense = '<='
        elif node.operator == Operator.EQ:
            # a = b → two constraints
            constraints = []
            # a - b ≤ 0
            expr1 = BinaryOpNode(Operator.SUBTRACT, node.left, node.right)
            constraints.append(self._extract_coefficients(expr1, '<=', 0.0))
            # -a + b ≤ 0
            neg_left = UnaryOpNode(Operator.NEGATE, node.left)
            expr2 = BinaryOpNode(Operator.ADD, neg_left, node.right)
            constraints.append(self._extract_coefficients(expr2, '<=', 0.0))
            return constraints

        return [self._extract_coefficients(expr, sense, constant)]

    def _extract_coefficients(self, expr: ExpressionNode, sense: str, constant: float) -> Constraint:
        # Extract variable coefficients from expression
        coefficient_extractor = CoefficientExtractor()
        coefficients = coefficient_extractor.extract(expr)
        return Constraint(coefficients, constant, sense, str(expr))
```

### 4. Canonical Transformation

```python
def to_canonical_form(comparison: ComparisonNode) -> List[Constraint]:
    """Transform comparison to canonical LP constraints."""
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
```

### 5. DECISION(x, size=N) Parsing

```python
class DSLParser:
    def parse_decision(self, function_call: FunctionCallNode) -> Dict[str, Any]:
        """Parse DECISION(x, size=N) function call."""
        if len(function_call.arguments) < 1:
            raise ValueError("DECISION requires at least variable name")

        # First argument is variable name
        var_name_node = function_call.arguments[0]
        if not isinstance(var_name_node, VariableNode):
            raise ValueError("DECISION first argument must be variable name")

        var_name = var_name_node.name
        size = 1  # Default size

        # Check for size parameter
        if len(function_call.arguments) > 1:
            # Look for keyword argument size=N
            for i in range(1, len(function_call.arguments)):
                arg = function_call.arguments[i]
                if isinstance(arg, BinaryOpNode) and arg.operator == Operator.EQ:
                    if isinstance(arg.left, VariableNode) and arg.left.name == 'size':
                        if isinstance(arg.right, ConstantNode):
                            size = int(arg.right.value)

        # Generate vector variable names
        vector_vars = []
        if size > 1:
            vector_vars = [f"{var_name}{i+1}" for i in range(size)]
        else:
            vector_vars = [var_name]

        return {
            'type': 'DECISION',
            'variable_name': var_name,
            'size': size,
            'vector_variables': vector_vars
        }
```

### 6. DSL Detection Pipeline

```python
class DSLDetector(ExpressionVisitor):
    def __init__(self):
        self.dsl_functions = []

    def visit_function_call(self, node: FunctionCallNode):
        function_name = node.function_name.upper()

        if function_name == 'DECISION':
            dsl_info = self._parse_decision(node)
            self.dsl_functions.append(dsl_info)
        elif function_name == 'BOUND':
            dsl_info = self._parse_bound(node)
            self.dsl_functions.append(dsl_info)
        elif function_name == 'OBJECTIVE':
            dsl_info = self._parse_objective(node)
            self.dsl_functions.append(dsl_info)

        # Continue visiting arguments
        for arg in node.arguments:
            arg.accept(self)
```

## III. POWERSHELL SAFE INTEGRATION PLAN

### 1. Input Normalization Pipeline

**Step-by-Step Process**:

1. **UTF-8 Decoding**: Force UTF-8 with fallback replacement
   ```python
   text = text.decode('utf-8', errors='replace')
   ```
2. **Unicode Normalization**: NFKC form for compatibility
3. **Operator Replacement**: Unicode → ASCII operators
4. **Line Ending Normalization**: CRLF → LF
5. **Tab Normalization**: Tabs → spaces (optional)

### 2. CLI-Safe Execution Flow

**PowerShell Command Examples**:

```powershell
# Run tests with UTF-8 encoding
python -c "import sys; print(sys.getdefaultencoding())"
$env:PYTHONIOENCODING="utf-8"
python test_week2.py

# Run parser with input from file
Get-Content input.txt -Encoding UTF8 | python parse_formula.py

# Safe piping with encoding
$input = "x ≤ y"
$input | Out-File -Encoding UTF8 temp.txt
python parse_formula.py temp.txt
```

### 3. CRLF Normalization Strategy

**Implementation**:

```python
def normalize_line_endings(text: str) -> str:
    """Normalize Windows CRLF to Unix LF."""
    # Replace CRLF with LF
    text = text.replace('\r\n', '\n')
    # Replace any remaining CR with LF
    text = text.replace('\r', '\n')
    return text
```

### 4. Fallback Encoding Strategy

**Robust Decoding**:

```python
def safe_decode(data: bytes) -> str:
    """Safely decode bytes to string with multiple fallbacks."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']

    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    # Final fallback: replace errors
    return data.decode('utf-8', errors='replace')
```

### 5. PowerShell Integration Example

**Example PowerShell Script**:

```powershell
# PowerShell script for running Week-2 tests
param(
    [string]$InputFile,
    [string]$OutputFile = "results.json"
)

# Set UTF-8 encoding for PowerShell
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Read input with UTF-8
$inputText = Get-Content $InputFile -Encoding UTF8 -Raw

# Normalize line endings (PowerShell preserves them)
$inputText = $inputText -replace "`r`n", "`n"

# Run Python parser
$pythonScript = @"
import sys
from unicode_normalizer import UnicodeNormalizer

normalizer = UnicodeNormalizer()
normalized = normalizer.normalize(sys.argv[1])
print(normalized)
"@

$normalized = python -c $pythonScript -- $inputText

# Process with AST parser
$result = python -c "
from ast_expression_parser import parse_expression, extract_constraints
ast = parse_expression('$normalized')
constraints = extract_constraints(ast)
import json
print(json.dumps(constraints, indent=2))
"

# Save results
$result | Out-File $OutputFile -Encoding UTF8
Write-Host "Results saved to $OutputFile"
```

## IMPLEMENTATION REQUIREMENTS

### 1. AST-Only Parsing

- No regex parsing for constraints
- All parsing must go through AST
- Comparison operators parsed via Python's ast module

### 2. Normalization Before Parsing

- Unicode normalization happens BEFORE AST parsing
- ASCII operators used internally
- Original expressions preserved for debugging

### 3. Backward Compatibility

- Existing ASCII operators continue to work
- No breaking changes to existing API
- Week 1 tests must still pass

### 4. Isolated Normalization Logic

- `unicode_normalizer.py` module
- Single responsibility: text normalization
- Reusable across entire codebase

## CANONICAL RULES (MANDATORY)

1. `a ≤ b` → `a - b ≤ 0`
2. `a ≥ b` → `-a + b ≤ 0`
3. `a = b` → two constraints:
   - `a - b ≤ 0`
   - `-a + b ≤ 0`

## DSL REQUIREMENTS (MANDATORY)

### DECISION Function

- `DECISION(x)` → scalar variable `x`
- `DECISION(x, size=3)` → vector variables `x1, x2, x3`
- Size parameter must be positive integer

### BOUND Function

- `BOUND(x, lower, upper)` → variable bounds
- Lower/upper can be numbers or `None`
- Overrides any existing bounds

### OBJECTIVE Function

- `OBJECTIVE(expr)` → objective function
- Expression must be linear
- Converted to canonical minimization form

## ACCEPTANCE CRITERIA (WEEK-2)

1. ✅ Unicode operators parse correctly (≤, ≥, ＝)
2. ✅ Works in PowerShell environment
3. ✅ No UnicodeDecodeError occurs
4. ✅ DECISION(size=N) expands correctly
5. ✅ Paving test passes (existing test suite)

## RESTRICTIONS

### MUST DO:

- Focus only on Week-2 scope
- Extend existing AST foundation
- Maintain backward compatibility

### MUST NOT DO:

- Rewrite Week-1 implementation
- Change matrix builder logic
- Modify solver implementation
- Implement Week-3 features
