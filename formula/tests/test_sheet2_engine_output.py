import math
import sys
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
FORMULA_DIR = THIS_FILE.parents[1]
REPO_ROOT = THIS_FILE.parents[2]

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(FORMULA_DIR))

from formula.excel_sheet_models import sheet2_exact_model
from lp_model_parser import LPModelParser
from lp_matrix_builder_deterministic_complete import LPMatrixBuilder
from lp_solver import LPSolver


def test_sheet2_engine_output_projected_xmin_xmax():
    model = sheet2_exact_model()

    parser = LPModelParser()
    lp_spec = parser.detect_lp_formulas(model.formulas)

    builder = LPMatrixBuilder(model.scenario_context)
    matrices = builder.build_from_formulas(model.formulas, lp_spec)

    solver = LPSolver()
    result = solver.solve_from_matrices(matrices, maximize=True)

    assert result["success"] is True
    vars_order = matrices["variables"]
    x1 = float(result["x"][vars_order.index("x1")])
    x2 = float(result["x"][vars_order.index("x2")])
    r = float(result["x"][vars_order.index("r")])

    alpha = float(model.expected_A_ub[1][2])
    beta = float(model.expected_A_ub[3][2])

    # What engine would show as projected min/max ranges for each variable.
    x1_min = x1 - alpha * r
    x1_max = x1 + alpha * r
    x2_min = x2 - beta * r
    x2_max = x2 + beta * r

    # Sheet2 constraint intervals
    x1_bound_min = -float(model.expected_b_ub[1])
    x1_bound_max = float(model.expected_b_ub[2])
    x2_bound_min = -float(model.expected_b_ub[3])
    x2_bound_max = float(model.expected_b_ub[4])

    assert x1_bound_min - 1e-6 <= x1_min <= x1_bound_max + 1e-6
    assert x1_bound_min - 1e-6 <= x1_max <= x1_bound_max + 1e-6
    assert x2_bound_min - 1e-6 <= x2_min <= x2_bound_max + 1e-6
    assert x2_bound_min - 1e-6 <= x2_max <= x2_bound_max + 1e-6

    # Expected output values for this exact Sheet2 fixture
    assert math.isclose(x1_min, 3800.0, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(x1_max, 3800.0, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(x2_min, 7800.0, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(x2_max, 7800.0, rel_tol=1e-6, abs_tol=1e-6)
