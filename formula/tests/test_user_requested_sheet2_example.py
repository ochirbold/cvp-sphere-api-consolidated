import math

from formula.lp.parser import LPModelParser
from formula.lp_matrix_builder_deterministic_complete import LPMatrixBuilder
from formula.lp_solver import LPSolver


def test_user_requested_sheet2_dsl_lp_example():
    # Input parameters provided by user
    p1, c1 = 15.0, 7.0
    p2, c2 = 17.0, 11.0
    f_cost = 2700.0
    xmin1, xmax1 = 0.0, 3800.0
    xmin2, xmax2 = 0.0, 7800.0

    cm1 = p1 - c1
    cm2 = p2 - c2
    cm_norm = math.sqrt(cm1**2 + cm2**2)

    # Optimizer DSL example:
    # - Includes user's objective and main constraint
    # - Adds x1<=r and x2<=r so with auto bounds the LP pins x1=x2=r at optimum
    dsl_formulas = {
        "DECISION_X": "DECISION(x,size=2)",
        "DECISION_R": "DECISION(r)",
        "OBJ": f"OBJECTIVE({cm1}*x1 + {cm2}*x2 - {cm_norm}*r)",
        "BOUND_R": "BOUND(r,0,None)",
        "CONSTRAINT_LP": f"-{cm1}*x1 - {cm2}*x2 + {cm_norm}*r <= -{f_cost}",
        "C_FIX_X1": "x1 - r <= 0",
        "C_FIX_X2": "x2 - r <= 0",
    }
    scenario_context = {
        "XMIN": [xmin1, xmin2],
        "XMAX": [xmax1, xmax2],
    }

    parser = LPModelParser()
    lp_spec = parser.detect_lp_formulas(dsl_formulas)

    builder = LPMatrixBuilder(scenario_context)
    matrices = builder.build_from_formulas(dsl_formulas, lp_spec)

    solver = LPSolver()
    result = solver.solve_from_matrices(matrices, maximize=True)

    assert result["success"] is True

    vars_order = matrices["variables"]
    x1 = float(result["x"][vars_order.index("x1")])
    x2 = float(result["x"][vars_order.index("x2")])
    r = float(result["x"][vars_order.index("r")])

    assert math.isclose(x1, 1900.0, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(x2, 1900.0, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(r, 1900.0, rel_tol=1e-6, abs_tol=1e-6)

    # Projected ranges follow optimizer's Sheet2 projection: p_j / ||p||
    p_norm = math.sqrt(p1**2 + p2**2)
    alpha1 = p1 / p_norm
    alpha2 = p2 / p_norm

    x1_min = x1 - alpha1 * r
    x1_max = x1 + alpha1 * r
    x2_min = x2 - alpha2 * r
    x2_max = x2 + alpha2 * r

    assert round(x1_min, 4) == 642.9189
    assert round(x1_max, 3) == 3157.081
    assert round(x2_min, 4) == 475.3081
    assert round(x2_max, 3) == 3324.692
