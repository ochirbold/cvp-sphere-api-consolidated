# Алдаагүй програмын хөгжүүлэлтийн төлөвлөгөө

## 1. Төслийн зорилго

**Эцсийн зорилго:** Шугаман програмыг өгөгдсөн pattern дагуу алдаагүй үр дүнг тооцон олж утга буцаах чадвартай систем.

**Шаардлага:**

1. DSL pattern-уудыг зөв таних
2. LP матрицуудыг алдаагүй бүтээх
3. SciPy solver-ыг зөв дуудах
4. Үр дүнг scenario_context-д алдаагүй шилжүүлэх
5. Phase 3 томьёог алдаагүй гүйцэтгэх

## 2. Хөгжүүлэлтийн дараалал

### **Phase 1: Суурь архитектур бэхжүүлэх** ✅ **(Дууссан)**

#### **1.1. DSL Formula Parser (`lp_model_parser.py`)**

- [x] `DECISION()` илрүүлэх
- [x] `OBJECTIVE()` илрүүлэх
- [x] `BOUND()` илрүүлэх
- [x] `<=`, `>=` хязгаарлалт илрүүлэх

#### **1.2. Constraint Parsing (`lp_matrix_builder.py`)**

- [x] `DOT(vector(CM_J), x)` илрүүлэх
- [x] `NORM(vector(CM_J))` илрүүлэх
- [x] Коэффициент гаргаж авах
- [x] Баруун талын тогтмол утга гаргаж авах

#### **1.3. LP Solver (`lp_solver.py`)**

- [x] `scipy.optimize.linprog` дуудах
- [x] Шийд гаргах

### **Phase 2: Vector Decision Variables дэмжих** 🔄 **(Одоо хэрэгжүүлэх)**

#### **2.1. `DECISION(x, size=N)` дэмжих**

```python
# Одоо:
DECISION(x) → variables = ["x"]

# Хэрэгжүүлэх:
DECISION(x, size=3) → variables = ["x1", "x2", "x3"]
```

**Файл:** `lp_model_parser.py`
**Алхам:**

1. `size` параметрийг шалгах
2. Вектор хувьсагчдын нэрс үүсгэх
3. `dsl_structures`-д хадгалах

#### **2.2. Vector variable mapping**

```python
# Одоо:
DOT(vector([10,6,8]), x) → coefficients = [-10, 0, 0, 0]

# Хэрэгжүүлэх:
DOT(vector([10,6,8]), x) → coefficients = [-10, -6, -8, 0]
```

**Файл:** `lp_matrix_builder.py`
**Алхам:**

1. `x` → `x1, x2, x3` буулгах логик нэмэх
2. Вектор коэффициент зөв гаргаж авах

### **Phase 3: Objective Parsing бүрэн хэрэгжүүлэх** 🔄

#### **3.1. `OBJECTIVE(DOT(vector(...), x))` дэмжих**

```python
# Одоо:
OBJECTIVE(DOT(vector(CM_J),x)) → c = [0.0, 0.0, 0.0, 0.0]

# Хэрэгжүүлэх:
OBJECTIVE(DOT(vector(CM_J),x)) → c = [-10, -6, -8, 0]
```

**Файл:** `lp_matrix_builder.py`
**Алхам:**

1. `_build_objective_vector()` аргыг бүрэн хэрэгжүүлэх
2. `DOT()` илэрхийллээс коэффициент гаргаж авах
3. Вектор хувьсагчдыг зөв буулгах

### **Phase 4: Complete LP Matrix Building** 🔄

#### **4.1. Бүрэн матрицууд бүтээх**

```python
# Одоо:
A_ub shape: 0x0
b_ub length: 0

# Хэрэгжүүлэх:
A_ub shape: 1x4
b_ub length: 1
```

**Файл:** `lp_matrix_builder.py`
**Алхам:**

1. `build_from_formulas()` аргыг бүрэн хэрэгжүүлэх
2. Бүх DSL бүрэлдэхүүн хэсгүүдийг нэгтгэх
3. Хэмжээ шалгах логик нэмэх

#### **4.2. Automatic constraints нэмэх**

```python
# CVP-д автоматаар нэмэх:
-x_j + r <= -xmin
x_j + r <= xmax
```

**Алхам:**

1. `_add_automatic_constraints()` аргыг бүрэн хэрэгжүүлэх
2. Scenario context-ээс bounds утгуудыг авах

### **Phase 5: Solution Propagation** 🔄

#### **5.1. LP шийдлийг scenario_context-д шилжүүлэх**

```python
# Хэрэгжүүлэх:
scenario_context["X0_J"] = x0  # [x1, x2, x3]
scenario_context["r0"] = r0    # scalar
```

**Файл:** `lp_solver.py`
**Алхам:**

1. Шийдлийг буцаах логик нэмэх
2. `scenario_context`-д утгуудыг хадгалах

#### **5.2. Phase 3 томьёог гүйцэтгэх**

```python
# Хэрэгжүүлэх:
SAFE_X_MIN = X0_J - r0 * (CM_J / CM_NORM)
SAFE_X_MAX = X0_J + r0 * (CM_J / CM_NORM)
```

**Файл:** `pythoncode.py`
**Алхам:**

1. Phase 3 томьёог гүйцэтгэх логик нэмэх
2. Үр дүнг rows-д шилжүүлэх

### **Phase 6: Туршилт ба баталгаажуулалт** 🔄

#### **6.1. Integration тестүүд**

```python
# Туршилтын жишээ:
test_complete_cvp_workflow()
test_vector_decision_variables()
test_objective_parsing()
test_constraint_parsing()
```

**Алхам:**

1. Бүрэн workflow тест үүсгэх
2. Алдааны тохиолдлуудыг тест хийх
3. Performance тест хийх

#### **6.2. Баталгаажуулалт**

```python
# Баталгаажуулалтын алхам:
1. DSL → LP matrices хувиргалт шалгах
2. LP шийдэл зөв эсэх шалгах
3. Scenario context шилжүүлэлт шалгах
4. Phase 3 үр дүн шалгах
```

## 3. Алдаагүй байдлын шаардлага

### **3.1. Error handling**

```python
try:
    # DSL parsing
    # LP matrix building
    # LP solving
    # Solution propagation
except Exception as e:
    # Алдааны мэдээлэл өгөх
    # Scenario context-д алдааны төлөв хадгалах
```

### **3.2. Validation checks**

```python
# 1. DSL syntax validation
# 2. Vector dimension validation
# 3. LP matrix dimension validation
# 4. Solution validation
# 5. Result propagation validation
```

### **3.3. Logging ба monitoring**

```python
# Дэлгэрэнгүй лог:
[INFO] DSL parsing started
[INFO] Decision variables: ['x1', 'x2', 'x3', 'r']
[INFO] Objective coefficients: [-10, -6, -8, 0]
[INFO] Constraint matrix shape: (1, 4)
[INFO] LP solution found: x0=[...], r0=...
[INFO] Scenario context updated
[INFO] Phase 3 formulas executed
```

## 4. Хэрэгжүүлэх дараалал (Priority)

### **Өндөр ач холбогдолтой:**

1. **Phase 2:** Vector Decision Variables дэмжих
2. **Phase 3:** Objective Parsing бүрэн хэрэгжүүлэх
3. **Phase 4:** Complete LP Matrix Building

### **Дунд ач холбогдолтой:**

4. **Phase 5:** Solution Propagation
5. **Phase 6:** Туршилт ба баталгаажуулалт

### **Бага ач холбогдолтой:**

6. Advanced features (матриц үйлдлүүд, илүү олон pattern төрлүүд)

## 5. Хүлээгдэж буй үр дүн

### **Phase 2 дууссаны дараа:**

- `DECISION(x, size=3)` ажиллана
- Вектор хувьсагчдыг зөв боловсруулна
- `DOT(vector(CM_J), x)` → `[-10, -6, -8, 0]` коэффициент гаргана

### **Phase 3 дууссаны дараа:**

- `OBJECTIVE(DOT(vector(CM_J), x))` зөв ажиллана
- `c` вектор зөв бүтээгдэнэ

### **Phase 4 дууссаны дараа:**

- Бүрэн LP матрицууд бүтээгдэнэ
- Automatic constraints нэмэгдэнэ

### **Phase 5 дууссаны дараа:**

- LP шийдэл scenario_context-д шилждэг
- Phase 3 томьёог гүйцэтгэдэг

### **Phase 6 дууссаны дараа:**

- Бүрэн integration тестүүд амжилттай гүйцэдэг
- Алдаагүй ажиллагаа баталгааждаг

## 6. Дүгнэлт

Энэхүү төлөвлөгөө нь төслийг алдаагүй, үр дүнтэй хөгжүүлэхэд чиглэгдсэн. Гол анхаарлыг **вектор хувьсагчдыг зөв боловсруулах**, **objective болон constraint parsing-ыг бүрэн хэрэгжүүлэх**, **LP матрицуудыг алдаагүй бүтээх** зэрэг суурь шатанд тавьсан.

Дээрх дарааллыг дагаж хэрэгжүүлснээр систем нь шугаман програмыг өгөгдсөн pattern дагуу алдаагүй үр дүнг тооцон олж утга буцаах чадвартай болно.
