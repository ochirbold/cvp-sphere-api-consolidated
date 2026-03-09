import math
import sys
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
FORMULA_DIR = THIS_FILE.parents[1]
REPO_ROOT = THIS_FILE.parents[2]

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(FORMULA_DIR))

from formula.excel_sheet_models import sheet1_exact_model, sheet2_exact_model
from lp_model_parser import LPModelParser
from lp_matrix_builder_deterministic_complete import LPMatrixBuilder
from lp_solver import LPSolver


def _build_and_solve(model):
    parser = LPModelParser()
    spec = parser.detect_lp_formulas(model.formulas)

    builder = LPMatrixBuilder(model.scenario_context)
    matrices = builder.build_from_formulas(model.formulas, spec)

    solver = LPSolver()
    result = solver.solve_from_matrices(matrices, maximize=True)
    return matrices, result


def _assert_matrix_close(actual, expected, tol=1e-6):
    assert len(actual) == len(expected)
    for r_idx, (a_row, e_row) in enumerate(zip(actual, expected)):
        assert len(a_row) == len(e_row)
        for c_idx, (a, e) in enumerate(zip(a_row, e_row)):
            assert math.isclose(a, e, rel_tol=tol, abs_tol=tol), (
                f"matrix mismatch at [{r_idx}][{c_idx}] got={a}, expected={e}"
            )


def test_excel_sheet1_exact_regression():
    model = sheet1_exact_model()
    matrices, result = _build_and_solve(model)

    # Objective row
    assert matrices["variables"] == model.expected_variables
    for i, (a, e) in enumerate(zip(matrices["c"], model.expected_c)):
        assert math.isclose(a, e, rel_tol=1e-6, abs_tol=1e-6), f"c[{i}] got={a}, expected={e}"

    # Constraint rows
    _assert_matrix_close(matrices["A_ub"], model.expected_A_ub)
    for i, (a, e) in enumerate(zip(matrices["b_ub"], model.expected_b_ub)):
        assert math.isclose(a, e, rel_tol=1e-6, abs_tol=1e-6), f"b_ub[{i}] got={a}, expected={e}"

    # Solution row
    assert result["success"] is True
    x1, r = result["x"]
    assert math.isclose(x1, model.expected_solution["x1"], rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(r, model.expected_solution["r"], rel_tol=1e-6, abs_tol=1e-6)

    excel_obj = model.expected_c[0] * x1 + model.expected_c[1] * r + model.objective_constant
    assert math.isclose(
        excel_obj,
        model.expected_solution["excel_objective"],
        rel_tol=1e-6,
        abs_tol=1e-6,
    )


def test_excel_sheet2_exact_regression():
    model = sheet2_exact_model()
    matrices, result = _build_and_solve(model)

    # Objective row
    assert matrices["variables"] == model.expected_variables
    for i, (a, e) in enumerate(zip(matrices["c"], model.expected_c)):
        assert math.isclose(a, e, rel_tol=1e-6, abs_tol=1e-6), f"c[{i}] got={a}, expected={e}"

    # Constraint rows
    _assert_matrix_close(matrices["A_ub"], model.expected_A_ub, tol=1e-5)
    for i, (a, e) in enumerate(zip(matrices["b_ub"], model.expected_b_ub)):
        assert math.isclose(a, e, rel_tol=1e-6, abs_tol=1e-6), f"b_ub[{i}] got={a}, expected={e}"

    # Solution row
    assert result["success"] is True
    x1, x2, r = result["x"]
    assert math.isclose(x1, model.expected_solution["x1"], rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(x2, model.expected_solution["x2"], rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(r, model.expected_solution["r"], rel_tol=1e-6, abs_tol=1e-6)

    excel_obj = (
        model.expected_c[0] * x1
        + model.expected_c[1] * x2
        + model.expected_c[2] * r
        + model.objective_constant
    )
    assert math.isclose(
        excel_obj,
        model.expected_solution["excel_objective"],
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
