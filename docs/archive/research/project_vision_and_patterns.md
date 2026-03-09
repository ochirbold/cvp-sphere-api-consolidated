# Төслийн зорилго болон Pattern архитектур

## 1. Төслийн ерөнхий зорилго

**Төслийн гол зорилго:** Бүхий төрлийн шугаман програмыг бодоход pattern үүсгэх замаар шугаман програмд шаардлагатай оролтуудыг тодорхойлж үр дүн авах.

**CVP-ийн үүрэг:** Зөвхөн туршилтын жишээ болгон ашиглагдаж байна. CVP нь төслийн бодит зорилгын нэг жишээ юм.

## 2. Pattern архитектур

### **2.1. DSL Pattern → LP Pattern**

```
DSL Pattern (Хэрэглэгчийн томьёо)
        │
        ▼
Abstract Syntax Tree (AST)
        │
        ▼
LP Pattern (Математик загвар)
        │
        ├── Decision Variables Pattern
        ├── Objective Pattern
        ├── Constraint Pattern
        └── Bound Pattern
        │
        ▼
LP Matrices (c, A_ub, b_ub, bounds)
```

### **2.2. Pattern төрлүүд**

#### **Decision Variables Pattern:**

```python
# Скаляр хувьсагч
DECISION(x)
DECISION(r)

# Вектор хувьсагч
DECISION(x, size=3)  # → x1, x2, x3

# Холимог хувьсагч
DECISION(production, size=5)
DECISION(inventory)
DECISION(cost)
```

#### **Objective Pattern:**

```python
# Энгийн objective
OBJECTIVE(DOT(vector(profit), production))

# Нарийн objective
OBJECTIVE(DOT(vector(revenue), sales) - DOT(vector(cost), production))

# Тогтмолтой objective
OBJECTIVE(DOT(vector(margin), volume) + fixed_cost)
```

#### **Constraint Pattern:**

```python
# Нэг хязгаарлалт
DOT(vector(resource_usage), production) <= available_resource

# Олон хязгаарлалт
production >= min_production
production <= max_production

# Нарийн хязгаарлалт
DOT(vector(material), production) <= material_budget
DOT(vector(labor), production) <= labor_hours
```

#### **Bound Pattern:**

```python
# Энгийн bounds
BOUND(production, 0, 1000)
BOUND(inventory, min_inv, max_inv)

# Вектор bounds
BOUND(production, [0,0,0], [100,200,300])

# Холимог bounds
BOUND(x, XMIN, XMAX)
BOUND(r, 0, None)
```

## 3. Generic LP Modeling Architecture

### **3.1. Оролтын pattern-ууд:**

```
[DSL Patterns] → [AST] → [LP Patterns] → [LP Matrices]
```

### **3.2. Pattern detection логик:**

```python
class LPPatternDetector:
    def detect_patterns(self, ast):
        patterns = {
            'decision_variables': self._detect_decisions(ast),
            'objective': self._detect_objective(ast),
            'constraints': self._detect_constraints(ast),
            'bounds': self._detect_bounds(ast)
        }
        return patterns

    def _detect_decisions(self, ast):
        # DECISION() илрүүлэх
        # size параметр шалгах
        # хувьсагчдын жагсаалт үүсгэх
        pass

    def _detect_objective(self, ast):
        # OBJECTIVE() илрүүлэх
        # DOT(), SUM(), etc илрүүлэх
        # Коэффициент гаргаж авах
        pass

    def _detect_constraints(self, ast):
        # <=, >=, == илрүүлэх
        # DOT(), NORM(), etc илрүүлэх
        # Коэффициент, тогтмол утгууд гаргаж авах
        pass

    def _detect_bounds(self, ast):
        # BOUND() илрүүлэх
        # Хувьсагч, доод, дээд хязгаарыг гаргаж авах
        pass
```

### **3.3. Pattern → Matrix хувиргалт:**

```python
class PatternToMatrixConverter:
    def convert(self, patterns, scenario_context):
        # 1. Decision variables → variables list
        variables = self._extract_variables(patterns['decision_variables'])

        # 2. Objective pattern → c vector
        c = self._build_c_vector(patterns['objective'], variables, scenario_context)

        # 3. Constraint patterns → A_ub, b_ub
        A_ub, b_ub = self._build_constraints(patterns['constraints'], variables, scenario_context)

        # 4. Bound patterns → bounds
        bounds = self._build_bounds(patterns['bounds'], variables, scenario_context)

        return {
            'c': c,
            'A_ub': A_ub,
            'b_ub': b_ub,
            'bounds': bounds,
            'variables': variables
        }
```

## 4. CVP жишээ: Pattern-ийн нэг төрөл

CVP нь дараах pattern-ийн жишээ юм:

### **CVP Pattern:**

```python
# Decision variables
DECISION(x, size=3)  # Production quantities
DECISION(r)          # Safety radius

# Objective: Maximize contribution margin
OBJECTIVE(DOT(vector(CM_J), x))

# Constraint: Budget constraint with safety
-DOT(vector(CM_J), x) + NORM(vector(CM_J)) * r <= F

# Bounds: Production limits
BOUND(x, XMIN, XMAX)
BOUND(r, 0, None)
```

### **CVP → Generic Pattern mapping:**

- `DECISION(x, size=3)` → Vector decision variable pattern
- `OBJECTIVE(DOT(vector(CM_J), x))` → Linear objective pattern
- `-DOT(vector(CM_J), x) + NORM(vector(CM_J)) * r <= F` → Linear constraint pattern
- `BOUND(x, XMIN, XMAX)` → Bound pattern

## 5. Бусад боломжит pattern-ууд

### **5.1. Production Planning Pattern:**

```python
DECISION(production, size=n_products)
DECISION(inventory, size=n_products)

OBJECTIVE(DOT(vector(profit), production) - DOT(vector(holding_cost), inventory))

# Capacity constraints
DOT(vector(machine_time), production) <= available_hours
DOT(vector(labor), production) <= available_labor

# Inventory balance
production + previous_inventory - demand == inventory

# Bounds
BOUND(production, min_production, max_production)
BOUND(inventory, safety_stock, max_inventory)
```

### **5.2. Portfolio Optimization Pattern:**

```python
DECISION(weight, size=n_assets)  # Portfolio weights

# Maximize return, minimize risk
OBJECTIVE(DOT(vector(expected_return), weight) - risk_aversion * DOT(weight, MATRIX(covariance), weight))

# Constraints
SUM(weight) == 1  # Fully invested
weight >= 0       # No short selling
DOT(vector(sector_exposure), weight) <= sector_limit
```

### **5.3. Transportation Pattern:**

```python
DECISION(shipment, size=n_sources*n_destinations)

# Minimize transportation cost
OBJECTIVE(DOT(vector(cost_per_unit), shipment))

# Supply constraints
SUM(shipment[source, :]) <= supply[source]

# Demand constraints
SUM(shipment[:, destination]) >= demand[destination]

# Non-negativity
BOUND(shipment, 0, None)
```

## 6. Дутуу хэсгүүд (Generic Pattern Support)

### **6.1. Vector Decision Variable Support**

- `DECISION(x, size=N)` дэмжих
- Вектор хувьсагчдыг зөв боловсруулах

### **6.2. Generic Objective Parsing**

- `DOT(vector, variable)` илрүүлэх
- Коэффициент гаргаж авах
- Тогтмол нэр томьёог боловсруулах

### **6.3. Generic Constraint Parsing**

- `<=`, `>=`, `==` илрүүлэх
- `DOT()`, `NORM()`, `SUM()` илрүүлэх
- Коэффициент, тогтмол утгууд гаргаж авах

### **6.4. Matrix Operations Support**

- `MATRIX()` илрүүлэх (квадрат хэлбэрийн хувьд)
- Матриц үржүүлэх дэмжих

## 7. Дүгнэлт

Төсөл нь **generic LP modeling platform** байх зорилготой. CVP нь зөвхөн энэ платформын нэг жишээ хэрэглээ юм.

**Гол ач холбогдол:** Pattern-уудыг илрүүлж, LP матрицууд руу автоматаар хувиргах чадвар.

**Ирээдүйн хөгжүүлэлт:**

1. Vector decision variables дэмжих
2. Generic objective болон constraint parsing
3. Илүү олон pattern төрлүүд дэмжих
4. Матриц үйлдлүүд дэмжих

Энэхүү архитектур нь аливаа шугаман програмчлалын асуудлыг DSL pattern-уудаар илэрхийлж, автоматаар шийдвэрлэх боломжийг олгоно.
