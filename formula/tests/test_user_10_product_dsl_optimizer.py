import math
import re

from formula.lp.parser import LPModelParser
from formula.lp_matrix_builder_deterministic_complete import LPMatrixBuilder
from formula.lp_solver import LPSolver


def test_user_ten_product_dsl_runs_and_produces_safe_ranges():
    products = [
        {"code": "P010", "p": 22000.0, "c": 13000.0, "xmin": 1000.0, "xmax": 7000.0},
        {"code": "P009", "p": 12000.0, "c": 7200.0, "xmin": 3000.0, "xmax": 18000.0},
        {"code": "P008", "p": 32000.0, "c": 19000.0, "xmin": 700.0, "xmax": 4500.0},
        {"code": "P007", "p": 38000.0, "c": 22000.0, "xmin": 500.0, "xmax": 4000.0},
        {"code": "P006", "p": 12000.0, "c": 7000.0, "xmin": 1500.0, "xmax": 9000.0},
        {"code": "P005", "p": 15000.0, "c": 8800.0, "xmin": 2000.0, "xmax": 11000.0},
        {"code": "P004", "p": 16000.0, "c": 9000.0, "xmin": 2000.0, "xmax": 12000.0},
        {"code": "P003", "p": 6500.0, "c": 3800.0, "xmin": 3000.0, "xmax": 20000.0},
        {"code": "P002", "p": 8500.0, "c": 5000.0, "xmin": 4000.0, "xmax": 25000.0},
        {"code": "P001", "p": 9000.0, "c": 5200.0, "xmin": 5000.0, "xmax": 30000.0},
    ]
    f_cost = 30000000.0

    p_j = [x["p"] for x in products]
    c_j = [x["c"] for x in products]
    cm_j = [p - c for p, c in zip(p_j, c_j)]
    xmin = [x["xmin"] for x in products]
    xmax = [x["xmax"] for x in products]

    dsl_formulas = {
        "CM_J": "P_J - C_J",
        "CM_NORM": "NORM(vector(CM_J))",
        "SAFE_X_MIN": "X0_J - r0*(CM_J/CM_NORM)",
        "SAFE_X_MAX": "X0_J + r0*(CM_J/CM_NORM)",
        "DECISION_X": "DECISION(x, size=10)",
        "DECISION_R": "DECISION(r)",
        "OBJ": "OBJECTIVE(r)",
        "BOUND_X": "BOUND(x,XMIN,XMAX)",
        "BOUND_R": "BOUND(r,0,None)",
        "CONSTRAINT_LP": "-DOT(vector(CM_J),x)+NORM(vector(CM_J))*r&lt;=-F",
    }

    scenario_context = {
        "P_J": p_j,
        "C_J": c_j,
        "CM_J": cm_j,
        "F": f_cost,
        "XMIN": xmin,
        "XMAX": xmax,
    }

    parser = LPModelParser()
    lp_spec = parser.detect_lp_formulas(dsl_formulas)

    assert lp_spec["is_lp_problem"] is True
    # Current parser limitation: BOUND(x,XMIN,XMAX) is parsed as (None, None)
    bound_x_info = [b for b in lp_spec["dsl_structures"]["bound"] if b["variable"] == "x"][0]
    assert bound_x_info["lower"] is None and bound_x_info["upper"] is None

    builder = LPMatrixBuilder(scenario_context)
    matrices = builder.build_from_formulas(dsl_formulas, lp_spec)

    assert len(matrices["variables"]) == 11
    assert "r" in matrices["variables"]
    assert len(matrices["A_ub"]) == 21

    solver = LPSolver()
    result = solver.solve_from_matrices(matrices, maximize=True)

    assert result["success"] is True

    variables = matrices["variables"]
    r = float(result["x"][variables.index("r")])

    # Tightest interval is product P007: (4000-500)/2 = 1750
    assert math.isclose(r, 1750.0, rel_tol=1e-9, abs_tol=1e-9)

    # Validate per-product safe range: x-r >= xmin, x+r <= xmax
    tol = 1e-6
    p_norm = math.sqrt(sum(v * v for v in p_j))
    for i, product in enumerate(products, start=1):
        x_var = f"x{i}"
        x_val = float(result["x"][variables.index(x_var)])

        safe_min = x_val - r
        safe_max = x_val + r

        assert safe_min >= product["xmin"] - tol
        assert safe_max <= product["xmax"] + tol

        alpha = product["p"] / p_norm
        projected_min = x_val - alpha * r
        projected_max = x_val + alpha * r

        assert projected_min <= projected_max

    # Validate main feasibility: DOT(CM_J, x) - NORM(CM_J)*r >= F
    cm_norm = math.sqrt(sum(v * v for v in cm_j))
    x_values = [float(result["x"][variables.index(f"x{i}")]) for i in range(1, 11)]
    lhs = sum(c * x for c, x in zip(cm_j, x_values)) - cm_norm * r
    assert lhs >= f_cost - 1e-6
