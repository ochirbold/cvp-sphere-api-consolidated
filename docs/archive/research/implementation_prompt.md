# Хөгжүүлэлтийн даалгаврын Prompt

## Даалгаврын зорилго

Development roadmap дагуу төслийг хөгжүүлэх. Hardcode hack ороогүй, spaghetti биш, алдаагүй архитектуртай байх.

## Архитектурын зарчим

1. **No hardcoding**: LP хувьсагчдын нэрсийг (`x`, `r`, `r0`) hardcode хийхгүй
2. **Modular design**: Жижиг, тусдаа логик блок
3. **Backward compatibility**: Одоо байгаа томьёо ажиллах
4. **Clean separation**: DSL parsing, LP matrix building, solving, propagation тусдаа

## Phase 2: Vector Decision Variables дэмжих

### Даалгавар 2.1: `DECISION(x, size=N)` дэмжих

**Файл:** `lp_model_parser.py`
**Зорилго:** `DECISION()` DSL-д `size` параметр нэмэх

**Хэрэгжүүлэх:**

```python
# Одоо:
DECISION(x) → variables = ["x"]

# Хэрэгжүүлэх:
DECISION(x, size=3) → variables = ["x1", "x2", "x3"]
```

**Алхам:**

1. `parse_dsl_structures()` арганд `size` параметрийг шалгах логик нэмэх
2. Вектор хувьсагчдын нэрс үүсгэх: `x1`, `x2`, `x3`, ...
3. `dsl_structures['decision']`-д хадгалах:
   ```python
   {
       'variable_name': 'x',
       'size': 3,
       'vector_variables': ['x1', 'x2', 'x3']
   }
   ```
4. `extract_decision_variables()` арганд вектор хувьсагчдыг нэмэх

**Шалгах:**

- `DECISION(x, size=3)` → `['x1', 'x2', 'x3']`
- `DECISION(r)` → `['r']` (size ороогүй тохиолдолд скаляр)
- `DECISION(production, size=5)` → `['production1', 'production2', ..., 'production5']`

### Даалгавар 2.2: Vector variable mapping

**Файл:** `lp_matrix_builder.py`
**Зорилго:** `DOT(vector(CM_J), x)` илэрхийлэлд `x`-г вектор хувьсагч гэж таних

**Хэрэгжүүлэх:**

```python
# Одоо:
DOT(vector([10,6,8]), x) → coefficients = [-10, 0, 0, 0]

# Хэрэгжүүлэх:
DOT(vector([10,6,8]), x) → coefficients = [-10, -6, -8, 0]
```

**Алхам:**

1. `_parse_constraint_formula()` арганд вектор хувьсагч буулгах логик нэмэх
2. `x` → `x1`, `x2`, `x3` буулгах:
   - `dsl_structures`-ээс вектор хувьсагчдын мэдээллийг авах
   - `x` нэртэй вектор хувьсагч байгаа эсэхийг шалгах
   - Хэрэв байвал `x1`, `x2`, `x3` хувьсагчдад коэффициент оноох
3. Вектор уртыг шалгах: вектор урт = хувьсагчийн тоо

**Шалгах:**

- `DOT(vector([10,6,8]), x)` → `[-10, -6, -8, 0]`
- `DOT(vector([5,7]), y)` (y нь `DECISION(y, size=2)`) → `[-5, -7, 0, 0]`
- Скаляр хувьсагчийн хувьд эхний элемент ашиглах

## Phase 3: Objective Parsing бүрэн хэрэгжүүлэх

### Даалгавар 3.1: `OBJECTIVE(DOT(vector(...), x))` дэмжих

**Файл:** `lp_matrix_builder.py`
**Зорилго:** Objective илэрхийллээс `c` вектор бүтээх

**Хэрэгжүүлэх:**

```python
# Одоо:
OBJECTIVE(DOT(vector(CM_J),x)) → c = [0.0, 0.0, 0.0, 0.0]

# Хэрэгжүүлэх:
OBJECTIVE(DOT(vector(CM_J),x)) → c = [-10, -6, -8, 0]
```

**Алхам:**

1. `_build_objective_vector()` аргыг бүрэн хэрэгжүүлэх:
   - `DOT()` илэрхийлэл илрүүлэх
   - Вектор нэр, хувьсагч нэрийг гаргаж авах
   - Scenario context-ээс векторыг авах
   - Вектор хувьсагч буулгах
   - Коэффициентуудыг `c` векторт оруулах
2. Negation handling: `-DOT(...)` → эсрэг тэмдэгтэй коэффициент

**Шалгах:**

- `OBJECTIVE(DOT(vector([10,6,8]), x))` → `c = [-10, -6, -8, 0]`
- `OBJECTIVE(-DOT(vector([5,7,9]), y))` → `c = [5, 7, 9, 0]`
- `OBJECTIVE(DOT(vector([a,b]), z) + 100)` → `c = [-a, -b, 0, 0]` (тогтмолыг үл тоомсорлох)

## Phase 4: Complete LP Matrix Building

### Даалгавар 4.1: Бүрэн матрицууд бүтээх

**Файл:** `lp_matrix_builder.py`
**Зорилго:** `build_from_formulas()` аргыг бүрэн хэрэгжүүлэх

**Хэрэгжүүлэх:**

```python
# Одоо:
A_ub shape: 0x0
b_ub length: 0

# Хэрэгжүүлэх:
A_ub shape: 1x4
b_ub length: 1
```

**Алхам:**

1. `build_from_formulas()` аргын бүх хэсгийг хэрэгжүүлэх:
   - Decision variables-ыг зөв олж авах
   - Objective vector бүтээх
   - Constraint матрицууд бүтээх
   - Bounds бүтээх
2. Хэмжээ шалгах логик нэмэх:
   - `c` vector length = decision variables count
   - `A_ub` columns = decision variables count
   - `A_ub` rows = constraints count
   - `b_ub` length = constraints count
   - `bounds` length = decision variables count

### Даалгавар 4.2: Automatic constraints нэмэх

**Зорилго:** CVP-д автоматаар bounds constraints нэмэх

**Хэрэгжүүлэх:**

```python
# CVP-д автоматаар нэмэх:
-x_j + r <= -xmin
x_j + r <= xmax
```

**Алхам:**

1. `_add_automatic_constraints()` аргыг бүрэн хэрэгжүүлэх:
   - `x` вектор хувьсагчдыг олох
   - `r` скаляр хувьсагчийг олох
   - Scenario context-ээс `xmin`, `xmax` утгуудыг авах
   - Автомат constraint үүсгэх
2. Хэрэв `xmin`/`xmax` байхгүй бол constraint нэмэхгүй

## Туршилтын даалгавар

### Тест 1: Vector Decision Variables

```python
def test_vector_decision_variables():
    # DECISION(x, size=3) → x1, x2, x3
    # DECISION(r) → r
    # Нийт хувьсагч: x1, x2, x3, r
    assert decision_variables == ['x1', 'x2', 'x3', 'r']
```

### Тест 2: Objective Parsing

```python
def test_objective_parsing():
    # OBJECTIVE(DOT(vector([10,6,8]), x))
    # → c = [-10, -6, -8, 0]
    assert c == [-10, -6, -8, 0]
```

### Тест 3: Constraint Parsing

```python
def test_constraint_parsing():
    # -DOT(vector([10,6,8]), x) + NORM(vector([10,6,8])) * r <= 2700
    # → A_ub = [[-10, -6, -8, 14.142]]
    # → b_ub = [2700]
    assert A_ub.shape == (1, 4)
    assert b_ub[0] == 2700
```

### Тест 4: Complete Workflow

```python
def test_complete_cvp_workflow():
    # 1. DSL parsing
    # 2. LP matrix building
    # 3. LP solving
    # 4. Solution propagation
    # 5. Phase 3 formulas
    assert scenario_context['X0_J'] == expected_x0
    assert scenario_context['r0'] == expected_r0
    assert rows[0]['SAFE_X_MIN'] == expected_safe_min
    assert rows[0]['SAFE_X_MAX'] == expected_safe_max
```

## Хэрэгжүүлэх дүрэм

1. **No hardcoding**: `x`, `r`, `r0` гэх мэт нэрсийг hardcode хийхгүй
2. **Modular functions**: Жижиг, тусдаа функцүүд
3. **Error handling**: Алдааны мэдээлэл өгөх
4. **Logging**: Дэлгэрэнгүй лог бичих
5. **Validation**: Оролтыг шалгах
6. **Backward compatibility**: Одоо байгаа код ажиллах

## Эхлэх цэг

1. Эхлээд `lp_model_parser.py`-г шинэчлэх: `DECISION(x, size=N)` дэмжих
2. Дараа нь `lp_matrix_builder.py`-г шинэчлэх: вектор хувьсагч буулгах
3. Objective parsing хэрэгжүүлэх
4. Complete matrix building хэрэгжүүлэх
5. Туршилт хийх

## Хүлээгдэж буй үр дүн

Phase 2, 3, 4 дууссаны дараа:

- `DECISION(x, size=3)` ажиллана
- `OBJECTIVE(DOT(vector(CM_J), x))` зөв ажиллана
- `-DOT(vector(CM_J), x) + NORM(vector(CM_J)) * r <= F` constraint зөв парсерддаг
- Бүрэн LP матрицууд бүтээгдэнэ
- CVP асуудлыг шийдэж чадна
