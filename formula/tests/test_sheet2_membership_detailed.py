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


def test_sheet2_solver_projected_ranges_within_constraints_detailed():
    model = sheet2_exact_model()

    # Step 1: Parse DSL -> LP spec
    parser = LPModelParser()
    spec = parser.detect_lp_formulas(model.formulas)

    # Step 2: Build LP matrices
    builder = LPMatrixBuilder(model.scenario_context)
    matrices = builder.build_from_formulas(model.formulas, spec)

    # Step 3: Solve LP (maximize)
    solver = LPSolver()
    result = solver.solve_from_matrices(matrices, maximize=True)

    assert result["success"] is True, f"Solver failed: {result.get('message')}"

    variables = matrices["variables"]
    idx_x1 = variables.index("x1")
    idx_x2 = variables.index("x2")
    idx_r = variables.index("r")

    x1 = float(result["x"][idx_x1])
    x2 = float(result["x"][idx_x2])
    r = float(result["x"][idx_r])

    # Alpha/Beta are coefficients of r in projected bound rows:
    # row1: -x1 + alpha*r <= -xmin1
    # row3: -x2 + beta*r  <= -xmin2
    alpha = float(model.expected_A_ub[1][2])
    beta = float(model.expected_A_ub[3][2])

    xmin1 = -float(model.expected_b_ub[1])
    xmax1 = float(model.expected_b_ub[2])
    xmin2 = -float(model.expected_b_ub[3])
    xmax2 = float(model.expected_b_ub[4])

    projected_x1_min = x1 - alpha * r
    projected_x1_max = x1 + alpha * r
    projected_x2_min = x2 - beta * r
    projected_x2_max = x2 + beta * r

    # Step 4: Membership checks (this is your main question)
    assert xmin1 - 1e-6 <= projected_x1_min <= xmax1 + 1e-6
    assert xmin1 - 1e-6 <= projected_x1_max <= xmax1 + 1e-6
    assert xmin2 - 1e-6 <= projected_x2_min <= xmax2 + 1e-6
    assert xmin2 - 1e-6 <= projected_x2_max <= xmax2 + 1e-6

    # Step 5: Main profitability constraint check
    main_row = model.expected_A_ub[0]
    main_rhs = model.expected_b_ub[0]
    lhs = main_row[0] * x1 + main_row[1] * x2 + main_row[2] * r
    assert lhs <= main_rhs + 1e-6

    # Step 6: Match the expected Sheet2 fixture solution
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
