# Математик загварын архитектур шинжилгээ

## 1. Ерөнхий архитектур

```
KPI_INDICATOR_INDICATOR_MAP
        │
        │ expression_string
        ▼
   DSL Formula Parser
        │
        ▼
   LP Model Builder
        │
        ├── objective → c vector
        ├── constraints → A_ub , b_ub
        └── bounds → bounds
        ▼
 scipy.optimize.linprog
        │
        ▼
   LP solution
        │
        ├── x0_j
        ├── r0
        ▼
scenario_context
        │
        ▼
SAFE_X_MIN / SAFE_X_MAX
```

## 2. DSL томьёоны төрөл

| DSL           | төрөл      | LP component |
| ------------- | ---------- | ------------ |
| `OBJECTIVE()` | objective  | c            |
| `BOUND()`     | bounds     | bounds       |
| `<=` `>=`     | constraint | A_ub         |
| `DECISION()`  | variable   | LP variable  |

## 3. Хэрэгжүүлсэн хэсгүүд

### ✅ **Бэлэн хэсгүүд:**

1. **DSL Formula Parser** (`lp_model_parser.py`)
   - `DECISION()` илрүүлэх
   - `OBJECTIVE()` илрүүлэх
   - `BOUND()` илрүүлэх
   - `<=`, `>=` хязгаарлалт илрүүлэх

2. **Constraint Parsing** (`lp_matrix_builder.py`)
   - `DOT(vector(CM_J), x)` илрүүлэх
   - `NORM(vector(CM_J))` илрүүлэх
   - Коэффициент гаргаж авах
   - Баруун талын тогтмол утга гаргаж авах

3. **LP Solver** (`lp_solver.py`)
   - `scipy.optimize.linprog` дуудах
   - Шийд гаргах

## 4. Дутуу хэсгүүд

### ❌ **Дутуу хэсгүүд:**

#### **4.1. Vector Decision Variables**

**Асуудал:** `DECISION(x)` зөвхөн скаляр хувьсагч үүсгэдэг
**Шаардлага:** `DECISION(x, size=3)` → `x1, x2, x3` вектор хувьсагч үүсгэх
**Шийдэл:** `lp_model_parser.py`-д `size` параметр дэмжих

```python
# Одоо:
DECISION(x) → variables = ["x"]

# Хэрэгжүүлэх ёстой:
DECISION(x, size=3) → variables = ["x1", "x2", "x3"]
```

#### **4.2. Objective Vector Building**

**Асуудал:** `OBJECTIVE(DOT(vector(CM_J),x))` → `c` вектор зөв бүтээгдэхгүй
**Шаардлага:** `DOT()` илэрхийллээс коэффициент гаргаж авах
**Шийдэл:** `_build_objective_vector()` аргыг бүрэн хэрэгжүүлэх

```python
# Одоо:
OBJECTIVE(DOT(vector(CM_J),x)) → c = [0.0, 0.0, 0.0, 0.0]

# Хэрэгжүүлэх ёстой:
OBJECTIVE(DOT(vector(CM_J),x)) → c = [-10, -6, -8, 0]
```

#### **4.3. Vector Variable Mapping in Constraints**

**Асуудал:** `DOT(vector(CM_J), x)` → `x`-г вектор гэж танихгүй
**Шаардлага:** `x` → `x1, x2, x3` гэж буулгах
**Шийдэл:** `_parse_constraint_formula()` аргыг сайжруулах

```python
# Одоо:
DOT(vector([10,6,8]), x) → coefficients = [-10, 0, 0, 0]

# Хэрэгжүүлэх ёстой:
DOT(vector([10,6,8]), x) → coefficients = [-10, -6, -8, 0]
```

#### **4.4. Complete LP Matrix Building**

**Асуудал:** Бүрэн `c`, `A_ub`, `b_ub`, `bounds` матрицууд бүтээгдэхгүй
**Шаардлага:** Бүх DSL бүрэлдэхүүн хэсгүүдийг нэгтгэх
**Шийдэл:** `build_from_formulas()` аргыг бүрэн хэрэгжүүлэх

```python
# Одоо:
A_ub shape: 0x0
b_ub length: 0

# Хэрэгжүүлэх ёстой:
A_ub shape: 1x4
b_ub length: 1
```

#### **4.5. Scenario Context Update**

**Асуудал:** LP шийдлийг `scenario_context`-д шилжүүлэхгүй
**Шаардлага:** `x0`, `r0` утгуудыг хадгалах
**Шийдэл:** `lp_solver.py`-д шийдлийг буцаах логик нэмэх

```python
# Хэрэгжүүлэх ёстой:
scenario_context["X0_J"] = x0  # [x1, x2, x3]
scenario_context["r0"] = r0    # scalar
```

#### **4.6. Safe Region Computation**

**Асуудал:** `SAFE_X_MIN`, `SAFE_X_MAX` тооцоолохгүй
**Шаардлага:** Математик томьёог хэрэгжүүлэх
**Шийдэл:** Phase 3-т томьёог гүйцэтгэх

```python
# Хэрэгжүүлэх ёстой:
SAFE_X_MIN = X0_J - r0 * (CM_J / CM_NORM)
SAFE_X_MAX = X0_J + r0 * (CM_J / CM_NORM)
```

## 5. Математик загвар

### **Objective:**

```
max ∑ h_j * x_j
= minimize -DOT(h, x)
c = [-h1, -h2, -h3, 0]
```

### **Constraint:**

```
-hx + ||h||r ≤ -F
A_ub = [[-h1, -h2, -h3, ||h||]]
b_ub = [-F]
```

### **Bounds:**

```
x1 ∈ [xmin1, xmax1]
x2 ∈ [xmin2, xmax2]
x3 ∈ [xmin3, xmax3]
r  ∈ [0, ∞]
```

## 6. Хэрэгжүүлэх дараалал

### **Phase 1: Vector Decision Variables**

1. `DECISION(x, size=3)` дэмжих
2. `x1, x2, x3` хувьсагч үүсгэх
3. `lp_model_parser.py` шинэчлэх

### **Phase 2: Objective Parsing**

1. `OBJECTIVE(DOT(vector(...), x))` дэмжих
2. `c` вектор зөв бүтээх
3. `_build_objective_vector()` бүрэн хэрэгжүүлэх

### **Phase 3: Constraint Parsing Enhancement**

1. `x` → `x1, x2, x3` буулгах
2. Вектор коэффициент зөв гаргаж авах
3. `_parse_constraint_formula()` сайжруулах

### **Phase 4: Complete Matrix Building**

1. Бүх матрицуудыг зөв хэмжээтэй бүтээх
2. `build_from_formulas()` бүрэн хэрэгжүүлэх
3. Хэмжээ шалгах логик нэмэх

### **Phase 5: Solution Propagation**

1. LP шийдлийг `scenario_context`-д шилжүүлэх
2. `X0_J`, `r0` утгуудыг хадгалах
3. Phase 3 томьёог гүйцэтгэх

## 7. Оролцсон файлууд

### **Үндсэн файлууд:**

1. `lp_model_parser.py` - DSL парсер
2. `lp_matrix_builder.py` - LP матриц бүтээгч
3. `lp_solver.py` - LP шийдвэрлэгч
4. `pythoncode.py` - Гурван үе шаттай гүйцэтгэл

### **Туршилтын файлууд:**

1. `test_simple_constraint_parser.py` - Constraint parsing тест
2. `test_simple_correct_formulation.py` - Зөв математик загвар
3. `test_constraint_implementation.py` - Хэрэгжүүлэлтийн тест

## 8. Дүгнэлт

Төсөл нь математик загварын архитектурын үндэс суурийг тавьсан. Гол дутуу хэсэг нь **вектор хувьсагчдыг зөв боловсруулах** явдал юм. `DECISION(x, size=3)` дэмжиж, `DOT(vector(CM_J), x)` илэрхийлэлд `x`-г `x1, x2, x3` вектор хувьсагч гэж таньж, коэффициентүүдийг зөв гаргаж авах нь хамгийн чухал алхам юм.

Бүх дутуу хэсгүүдийг хэрэгжүүлснээр систем нь:

1. DSL томьёог LP матриц болгон хувиргах
2. SciPy ашиглан оновчтой шийд олох
3. Шийдлийг scenario_context-д шилжүүлэх
4. SAFE_X_MIN, SAFE_X_MAX тооцоолох

бүрэн ажиллагаатай математик загварчлалын платформ болно.
