from formula.excel_sheet_models import sheet2_exact_model
from formula.lp_model_parser import LPModelParser
from formula.lp_matrix_builder_deterministic_complete import LPMatrixBuilder
from formula.lp_solver import LPSolver


def run_trial():
    model = sheet2_exact_model()

    parser = LPModelParser()
    spec = parser.detect_lp_formulas(model.formulas)

    builder = LPMatrixBuilder(model.scenario_context)
    matrices = builder.build_from_formulas(model.formulas, spec)

    solver = LPSolver()
    result = solver.solve_from_matrices(matrices, maximize=True)

    if not result.get("success"):
        return {"success": False, "message": result.get("message")}

    vars_order = matrices["variables"]
    x1 = float(result["x"][vars_order.index("x1")])
    x2 = float(result["x"][vars_order.index("x2")])
    r = float(result["x"][vars_order.index("r")])

    alpha = float(model.expected_A_ub[1][2])
    beta = float(model.expected_A_ub[3][2])

    # Sheet2 I/K equivalent projected ranges
    p1_min = x1 - alpha * r
    p1_max = x1 + alpha * r
    p2_min = x2 - beta * r
    p2_max = x2 + beta * r

    return {
        "success": True,
        "solver": {"x1": x1, "x2": x2, "r": r},
        "projected": [
            {"itemCode": "P1", "projectedMin": p1_min, "projectedMax": p1_max},
            {"itemCode": "P2", "projectedMin": p2_min, "projectedMax": p2_max},
        ],
        "bounds": [
            {"itemCode": "P1", "xmin": 0.0, "xmax": 3800.0},
            {"itemCode": "P2", "xmin": 0.0, "xmax": 7800.0},
        ],
    }


if __name__ == "__main__":
    out = run_trial()
    print(out)
